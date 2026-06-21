# Logician

**Deterministic Policy Enforcement Layer for Sovereign AI Systems**

A practical implementation of the ResonantOS "Logician" (Symbiotic Shield) concept — a deterministic rule engine that sits between a probabilistic LLM (the Oracle) and actual execution.

## Purpose

While LLMs are excellent at synthesis and ideation, they are unreliable at consistently following complex rules, boundaries, and constitutions. The Logician enforces non-negotiable policies in a deterministic, auditable, and bypass-resistant way.

This repo contains the **VIGIL Logician v0.1**, built for the [Sovereign Intelligence Network](https://github.com/vonstegen/drt-ternary-network-system) and specifically tuned to enforce the rules in [SOUL.md](https://github.com/vonstegen/drt-ternary-network-system/blob/main/Docs/SOUL.md).

## Core Features

- **Deterministic Rules**: Pure Python, no LLM calls in the critical path (ALLOW / HOLD / DENY verdicts with full trace)
- **SOUL.md Enforcement**: Memory boundaries, injection resistance, sovereign mode, Matrix gateway integrity, quiet hours, constitutional resilience
- **Integration**: Works with `guardian-verify.sh` to prevent hallucinations in Matrix/Element X reports
- **Audit Trail**: Every decision is logged for observability and future self-improvement loops
- **Extensible**: Easy to add new rules as the constitution evolves

## Quick Start

```bash
cd logician
python3 scripts/vigil_logician.py
```

See `Docs/ResonantOS-Logician.md` for the original architectural essay and `scripts/vigil_logician.py` for the implementation.

## Repository Structure

- `Docs/` — Reference materials and audits (Claude 3.5 Sonnet + GPT-4o reviews)
- `scripts/` — Core `vigil_logician.py` and `guardian-verify.sh`
- `research/` — Scientific documentation and experiments

## Related Projects

- [drt-ternary-network-system](https://github.com/vonstegen/drt-ternary-network-system) — Primary research workspace where this was developed
- ResonantOS concept by Augmented Mind (Substack)

## License

MIT — feel free to adapt for your own sovereign AI systems.

---

**"The Oracle proposes. The Logician disposes."**

Built as part of the Ternary Rod Rig project to make VIGIL (and similar systems) a truly trustworthy, fixed-point AI partner that does what it says it will do.
