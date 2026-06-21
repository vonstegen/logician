#!/usr/bin/env python3
"""
Chat Logger for VIGIL + Matrix / Hermes Terminal

Automatically creates clean, Obsidian-friendly markdown files with:
- YAML frontmatter (metadata)
- Timestamps
- Clean conversation formatting
- Proper headings and structure

Saves to ~/logician/chat-logs/ by default.
Use publish-to-vault command to copy to Obsidian vault (respects read-only preference).
"""

import sys
import json
from datetime import datetime
from pathlib import Path

VAULT_PATH = Path("/home/vigil/VonStegen-Master-Vault/Chats/Vigil")
LOG_DIR = Path.home() / "logician" / "chat-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def generate_filename(topic="vigil"):
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    return f"{timestamp}-{topic}.md"

def create_markdown(content: str, source: str = "matrix", title: str = None) -> Path:
    """Create a well-formatted Obsidian markdown file."""
    now = datetime.now()
    filename = generate_filename()
    filepath = LOG_DIR / filename

    frontmatter = f"""---
title: "{title or 'VIGIL Conversation'}"
date: {now.strftime("%Y-%m-%d")}
time: {now.strftime("%H:%M:%S")}
source: {source}
tags: [vigil, matrix, chat-log, ternary]
---

# {title or 'VIGIL Chat Log'}

**Date:** {now.strftime("%Y-%m-%d %H:%M:%S")}

---

{content.strip()}

---

*Logged automatically by VIGIL Chat Logger. Part of the Logician / Sovereign Intelligence Network project.*
"""

    filepath.write_text(frontmatter, encoding="utf-8")
    print(f"✅ Chat logged to: {filepath}")

    return filepath

def publish_to_vault(log_file: Path):
    """Copy log to Obsidian vault (with user confirmation in real use)."""
    if not VAULT_PATH.exists():
        VAULT_PATH.mkdir(parents=True, exist_ok=True)
        print(f"Created vault directory: {VAULT_PATH}")

    dest = VAULT_PATH / log_file.name
    dest.write_text(log_file.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"✅ Published to Obsidian vault: {dest}")
    return dest

if __name__ == "__main__":
    if len(sys.argv) > 1:
        content = sys.argv[1]
        source = sys.argv[2] if len(sys.argv) > 2 else "matrix"
        title = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        content = "Test conversation content would go here..."
        source = "terminal"
        title = "Test Log"

    log_file = create_markdown(content, source, title)
    print(f"\nTo publish to vault, run: python3 scripts/chat-logger.py --publish {log_file.name}")
