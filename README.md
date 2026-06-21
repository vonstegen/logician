# Logician

**Deterministic Policy Enforcement + Automatic Chat Logging for Sovereign AI**

This repository contains the **VIGIL Logician** (Symbiotic Shield) and a fully automatic chat logging system for Matrix (Element X) and Hermes terminal conversations.

## Components

### 1. VIGIL Logician (`scripts/vigil_logician.py`)
Deterministic rule engine that enforces SOUL.md rules before any action or Matrix report. Prevents hallucinations and ensures VIGIL "does what it says."

### 2. Automatic Chat Logger (`scripts/chat-logger.py` + `start-vigil-logger.sh`)
**Fully automatic** logging of all conversations:
- Matrix / Element X chats with VIGIL
- Hermes terminal sessions

**Features:**
- Clean Obsidian-ready markdown with YAML frontmatter
- Timestamps, tags, metadata
- Saves to `chat-logs/`
- Automatically publishes to `~/VonStegen-Master-Vault/Chats/Vigil/`

## Quick Start — Automatic Logging

```bash
cd ~/logician
./scripts/start-vigil-logger.sh
```

This will:
- Restart the Hermes gateway with logging enabled
- Start a background processor that converts conversations into beautiful markdown files
- Automatically publish them to your Obsidian vault under `Chats/Vigil/`

## Files

- `scripts/vigil_logician.py` — The deterministic Logician
- `scripts/chat-logger.py` — Core logging engine (v2.0)
- `scripts/start-vigil-logger.sh` — Launches everything automatically
- `scripts/guardian-verify.sh` — Companion verification tool
- `Docs/` — Reference materials and audits (Claude 3.5 Sonnet + GPT-4o)

## Philosophy

"The Oracle proposes. The Logician disposes."

All conversations are now automatically preserved as clean, searchable, dated Obsidian notes. No more lost context. Full audit trail for the Ternary Rod Rig project and beyond.

---

Built as part of the Sovereign Intelligence Network. See [drt-ternary-network-system](https://github.com/vonstegen/drt-ternary-network-system) for the main research workspace.

Last updated: 2026-06-20
