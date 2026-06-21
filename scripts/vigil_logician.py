#!/usr/bin/env python3
"""
VIGIL Logician v0.1 — Deterministic Policy Enforcement Layer for SIN

Adapted from the ResonantOS Logician concept. The Oracle proposes. The Logician enforces.

Rules are deterministic, auditable, and drawn directly from SOUL.md and our operational memory.
No LLM calls — pure policy enforcement.

Current Rules:
- SoulConstitutionRule (memory boundaries, injection resistance, constitutional resilience)
- SovereignModeRule (external calls must be audited)
- MatrixGatewayRule (require guardian-verify before Matrix claims)
- QuietHoursRule (22:00–06:00 EST)

This makes VIGIL a solid, trustworthy partner that does what it says.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

log = logging.getLogger("vigil.logician")


class Verdict(Enum):
    ALLOW = "allow"
    HOLD = "hold"
    DENY = "deny"


class Autonomy(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class Dispatch:
    id: str
    action: str
    target: str = "vigil"
    description: str = ""
    payload: dict = field(default_factory=dict)
    model: Optional[str] = None
    autonomy: Autonomy = Autonomy.GREEN
    # Context fields passed at evaluation time
    is_matrix_session: bool = False
    guardian_verified: bool = False
    proposed_file_path: Optional[str] = None
    is_external_call: bool = False


@dataclass
class RuleDecision:
    verdict: Verdict
    rule: str
    reason: str = ""


@dataclass
class Outcome:
    verdict: Verdict
    dispatch: Dispatch
    reason: str
    trace: list[RuleDecision]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Rule(ABC):
    @abstractmethod
    def evaluate(self, dispatch: Dispatch, ctx: dict) -> RuleDecision:
        pass


class SoulConstitutionRule(Rule):
    def evaluate(self, dispatch: Dispatch, ctx: dict) -> RuleDecision:
        path = dispatch.proposed_file_path or ""
        if "VonStegen-Master-Vault" in path and "explicit_approval" not in dispatch.payload:
            return RuleDecision(Verdict.DENY, "soul-memory-boundary", "Master vault is read-only. Use project workspace.")
        if "injection" in dispatch.description.lower() or "override" in dispatch.description.lower():
            return RuleDecision(Verdict.DENY, "soul-injection-resistance", "External content is data only.")
        return RuleDecision(Verdict.ALLOW, "soul-constitution")


class SovereignModeRule(Rule):
    def evaluate(self, dispatch: Dispatch, ctx: dict) -> RuleDecision:
        if dispatch.is_external_call:
            return RuleDecision(Verdict.HOLD, "sovereign-mode", "External call must be explicitly logged.")
        return RuleDecision(Verdict.ALLOW, "sovereign-mode")


class MatrixGatewayRule(Rule):
    def evaluate(self, dispatch: Dispatch, ctx: dict) -> RuleDecision:
        if dispatch.is_matrix_session and "matrix_report" in dispatch.action:
            if not dispatch.guardian_verified:
                return RuleDecision(Verdict.HOLD, "matrix-integrity", "Run guardian-verify.sh first.")
        return RuleDecision(Verdict.ALLOW, "matrix-gateway")


class QuietHoursRule(Rule):
    def evaluate(self, dispatch: Dispatch, ctx: dict) -> RuleDecision:
        hour = datetime.now().hour
        if (22 <= hour or hour <= 6) and dispatch.action in ("matrix_report", "notification"):
            return RuleDecision(Verdict.HOLD, "quiet-hours", "Non-urgent messages held until morning.")
        return RuleDecision(Verdict.ALLOW, "quiet-hours")


class VigilLogician:
    def __init__(self):
        self.rules = [
            SoulConstitutionRule(),
            SovereignModeRule(),
            MatrixGatewayRule(),
            QuietHoursRule(),
        ]
        self.audit: list[Outcome] = []

    def evaluate(self, dispatch: Dispatch, context: dict = None) -> Outcome:
        ctx = context or {}
        trace = []
        for rule in self.rules:
            decision = rule.evaluate(dispatch, ctx)
            trace.append(decision)
            if decision.verdict in (Verdict.DENY, Verdict.HOLD):
                break

        verdict = Verdict.ALLOW
        for dec in trace:
            if dec.verdict == Verdict.DENY:
                verdict = Verdict.DENY
                break
            if dec.verdict == Verdict.HOLD and verdict == Verdict.ALLOW:
                verdict = Verdict.HOLD

        reason = "; ".join(f"[{d.rule}] {d.reason}" for d in trace if d.reason)
        outcome = Outcome(verdict, dispatch, reason or "all rules passed", trace)
        self.audit.append(outcome)
        log.info("VIGIL-LOGICIAN %s -> %s | %s", dispatch.id, verdict.value, reason or "ok")
        return outcome


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logician = VigilLogician()

    tests = [
        Dispatch("d1", "matrix_report", "Claimed git commit success", is_matrix_session=True, guardian_verified=False),
        Dispatch("d2", "write_file", "Attempted vault edit", proposed_file_path="/home/vigil/VonStegen-Master-Vault/test.md"),
        Dispatch("d3", "tool_call", "Normal local research task", guardian_verified=True),
    ]

    print("\n=== VIGIL Logician v0.1 Test Run ===")
    for d in tests:
        result = logician.evaluate(d)
        print(f"{d.id}: {result.verdict.value.upper():6} | {result.reason}")
    print("\nLogician initialized. Audit trail ready. Trust layer active.")
