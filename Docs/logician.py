"""
logician.py - The Logician: a deterministic policy/guardrail layer for the
HermesAgent dispatch loop (FAIS).

The Oracle (LLMs / agents) PROPOSES a DISPATCH envelope.
The Logician DISPOSES: every proposed dispatch passes through an ordered chain
of deterministic rules before it is allowed to reach a worker.

There are NO LLM calls in this file. Rules are pure, ordered, and composable.
Each rule returns one of:
    ALLOW  - pass through (optionally rewriting the dispatch, e.g. rerouting)
    HOLD   - blocked pending human ratification (your YELLOW gate)
    DENY   - hard blocked, with a reason

>>> Adjust the `Dispatch` dataclass field names to match your real envelope. <<<
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Callable, Optional

log = logging.getLogger("logician")


# --------------------------------------------------------------------------- #
# Core types
# --------------------------------------------------------------------------- #

class Verdict(Enum):
    ALLOW = "allow"
    HOLD = "hold"      # needs human ratification (yellow gate)
    DENY = "deny"      # hard blocked


class Autonomy(Enum):
    GREEN = "green"    # auto-proceed
    YELLOW = "yellow"  # require human ratification
    RED = "red"        # never auto-proceed


@dataclass
class Dispatch:
    """A proposed unit of work. ADJUST field names to match your real schema."""
    id: str
    kind: str                           # "code" | "research" | "trade" | ...
    target: str                         # node/agent: "pi-worker" | "lumen" | "vigil"
    payload: dict = field(default_factory=dict)

    # metadata the Logician reasons over
    model_route: Optional[str] = None   # "openrouter" | "local" | ...
    model: Optional[str] = None         # "claude-sonnet-4" | "qwen3:8b" | ...
    est_cost_usd: float = 0.0
    repo: Optional[str] = None          # repo this work touches, if any
    autonomy: Autonomy = Autonomy.GREEN


@dataclass
class RuleDecision:
    verdict: Verdict
    rule: str
    reason: str = ""
    transform: Optional[Dispatch] = None  # rewritten dispatch, if the rule edits it


@dataclass
class Outcome:
    verdict: Verdict
    dispatch: Dispatch                    # possibly transformed
    reason: str
    trace: list[RuleDecision]             # every rule's decision, for the audit log


# --------------------------------------------------------------------------- #
# Runtime context the rules read from
# --------------------------------------------------------------------------- #

@dataclass
class BudgetLedger:
    """The Logician only CHECKS budget here. Actual charging happens on
    execution / when a RESULT comes back -- not at evaluation time."""
    remaining_usd: float

    def can_afford(self, cost: float) -> bool:
        return cost <= self.remaining_usd

    def charge(self, cost: float) -> None:
        self.remaining_usd -= cost


@dataclass
class Context:
    budget: BudgetLedger
    sensitive_repos: set[str] = field(default_factory=set)
    local_route: str = "local"
    external_routes: set[str] = field(default_factory=lambda: {"openrouter"})


# --------------------------------------------------------------------------- #
# Rule base class
# --------------------------------------------------------------------------- #

class Rule(ABC):
    name: str = "rule"

    @abstractmethod
    def evaluate(self, d: Dispatch, ctx: Context) -> RuleDecision:
        ...

    # convenience constructors so concrete rules stay terse
    def allow(self, transform: Optional[Dispatch] = None, reason: str = "") -> RuleDecision:
        return RuleDecision(Verdict.ALLOW, self.name, reason, transform)

    def hold(self, reason: str) -> RuleDecision:
        return RuleDecision(Verdict.HOLD, self.name, reason)

    def deny(self, reason: str) -> RuleDecision:
        return RuleDecision(Verdict.DENY, self.name, reason)


# --------------------------------------------------------------------------- #
# The three starter rules
# --------------------------------------------------------------------------- #

class BudgetRule(Rule):
    """Deny if the estimated cost would blow the remaining budget (= budget governor)."""
    name = "budget"

    def evaluate(self, d: Dispatch, ctx: Context) -> RuleDecision:
        if d.est_cost_usd <= 0:
            return self.allow()
        if ctx.budget.can_afford(d.est_cost_usd):
            return self.allow()
        return self.deny(
            f"est ${d.est_cost_usd:.4f} exceeds remaining ${ctx.budget.remaining_usd:.4f}"
        )


class SensitiveRepoRoutingRule(Rule):
    """Proprietary repo work must never leave on an external route.
    Reroute to the local/open-weight route when possible; deny if it can't."""
    name = "sensitive_repo_routing"

    def evaluate(self, d: Dispatch, ctx: Context) -> RuleDecision:
        if not d.repo or d.repo not in ctx.sensitive_repos:
            return self.allow()
        if d.model_route in ctx.external_routes:
            if ctx.local_route:
                # drop the external model id; the local worker picks its own model
                rerouted = replace(d, model_route=ctx.local_route, model=None)
                return self.allow(
                    transform=rerouted,
                    reason=f"rerouted sensitive repo '{d.repo}': "
                           f"{d.model_route} -> {ctx.local_route}",
                )
            return self.deny(
                f"sensitive repo '{d.repo}' cannot use external route "
                f"'{d.model_route}' and no local route is configured"
            )
        return self.allow()


class AutonomyGateRule(Rule):
    """Traffic-light gate. green -> proceed, yellow -> human ratify, red -> blocked."""
    name = "autonomy_gate"

    def evaluate(self, d: Dispatch, ctx: Context) -> RuleDecision:
        if d.autonomy is Autonomy.GREEN:
            return self.allow()
        if d.autonomy is Autonomy.YELLOW:
            return self.hold("yellow gate: requires human ratification")
        return self.deny("red gate: action not permitted to auto-proceed")


# --------------------------------------------------------------------------- #
# The engine
# --------------------------------------------------------------------------- #

class Logician:
    def __init__(self, rules: list[Rule]):
        self.rules = rules
        self.audit: list[Outcome] = []

    def evaluate(self, d: Dispatch, ctx: Context) -> Outcome:
        working = d
        trace: list[RuleDecision] = []

        # every rule sees the (possibly already-transformed) working dispatch
        for rule in self.rules:
            decision = rule.evaluate(working, ctx)
            trace.append(decision)
            if decision.transform is not None:
                working = decision.transform

        # precedence: DENY > HOLD > ALLOW
        verdict = Verdict.ALLOW
        for dec in trace:
            if dec.verdict is Verdict.DENY:
                verdict = Verdict.DENY
            elif dec.verdict is Verdict.HOLD and verdict is Verdict.ALLOW:
                verdict = Verdict.HOLD

        reason = "; ".join(f"[{dec.rule}] {dec.reason}" for dec in trace if dec.reason)
        outcome = Outcome(verdict, working, reason, trace)
        self.audit.append(outcome)
        log.info("dispatch=%s verdict=%s :: %s", d.id, verdict.value, reason or "ok")
        return outcome

    def override(self, outcome: Outcome, operator: str, justification: str) -> Outcome:
        """Human force-allow of a HELD or DENIED dispatch. Logs who and why so the
        Logician stays observable, not silent. Feeds the strike-based learning loop:
        repeated overrides of the same rule signal a rule that is too tight."""
        log.warning(
            "OVERRIDE by %s on %s (was %s): %s",
            operator, outcome.dispatch.id, outcome.verdict.value, justification,
        )
        forced = Outcome(Verdict.ALLOW, outcome.dispatch,
                         f"override by {operator}: {justification}", outcome.trace)
        self.audit.append(forced)
        return forced


# --------------------------------------------------------------------------- #
# Where it plugs into the dispatch loop
# --------------------------------------------------------------------------- #

def handle_dispatch(
    raw: dict,
    logician: Logician,
    ctx: Context,
    publish_to_worker: Callable[[Dispatch], None],
    queue_for_ratification: Callable[[Outcome], None],
    publish_result: Callable[[str, str, str], None],
) -> None:
    """Single entry point for each message pulled off the dispatch stream.
    Wire the three callbacks to your real Redis publishers / ratification queue
    (e.g. ntfy or a Slack thread for the HOLD case)."""
    d = Dispatch(**raw)  # adjust to your (de)serialization
    outcome = logician.evaluate(d, ctx)

    if outcome.verdict is Verdict.ALLOW:
        publish_to_worker(outcome.dispatch)        # note: possibly rerouted
    elif outcome.verdict is Verdict.HOLD:
        queue_for_ratification(outcome)            # surfaces to you for ratify/override
    else:  # DENY
        publish_result(d.id, "denied", outcome.reason)


# --- Redis Streams consumer skeleton (wire stream/group names to your setup) ---
#
# import json, redis
# r = redis.Redis(host="aether", port=6379, decode_responses=True)
# STREAM, GROUP, CONSUMER = "fais:dispatch", "logician", "logician-1"
# try:
#     r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
# except redis.ResponseError:
#     pass  # group already exists
# while True:
#     resp = r.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=1, block=5000)
#     for _stream, messages in resp or []:
#         for msg_id, fields in messages:
#             raw = json.loads(fields["envelope"])
#             handle_dispatch(raw, logician, ctx,
#                             publish_to_worker, queue_for_ratification, publish_result)
#             r.xack(STREAM, GROUP, msg_id)


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ctx = Context(
        budget=BudgetLedger(remaining_usd=5.00),
        sensitive_repos={"fais-core", "baa-private"},
        local_route="local",
        external_routes={"openrouter"},
    )
    logician = Logician([
        BudgetRule(),
        SensitiveRepoRoutingRule(),
        AutonomyGateRule(),
    ])

    samples = [
        Dispatch("d1", "research", "lumen", model_route="openrouter",
                 model="kimi-k2", est_cost_usd=0.02, autonomy=Autonomy.GREEN),
        Dispatch("d2", "code", "pi-worker", model_route="openrouter",
                 model="claude-sonnet-4", repo="fais-core", est_cost_usd=0.10,
                 autonomy=Autonomy.GREEN),
        Dispatch("d3", "trade", "lumen", est_cost_usd=0.0, autonomy=Autonomy.YELLOW),
        Dispatch("d4", "research", "lumen", model_route="openrouter",
                 est_cost_usd=9.99, autonomy=Autonomy.GREEN),
        Dispatch("d5", "deploy", "vigil", autonomy=Autonomy.RED),
    ]

    print("\n--- evaluations ---")
    for s in samples:
        out = logician.evaluate(s, ctx)
        print(f"{s.id:>3} -> {out.verdict.value.upper():5} | "
              f"route={out.dispatch.model_route} | {out.reason or 'ok'}")
