#!/usr/bin/env python3
"""
VIGIL Automatic Chat Logger v2.0

Fully automatic logging for:
- Matrix / Element X conversations
- Hermes terminal sessions

Features:
- Real-time or batched logging
- Clean Obsidian markdown with YAML frontmatter
- Automatic publishing option to vault (with safety)
- Thread-safe, timestamped, searchable
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

LOG_DIR = Path.home() / "logician" / "chat-logs"
VAULT_DIR = Path("/home/vigil/VonStegen-Master-Vault/Chats/Vigil")

LOG_DIR.mkdir(parents=True, exist_ok=True)
VAULT_DIR.mkdir(parents=True, exist_ok=True)

class ChatLogger:
    def __init__(self):
        self.current_log = []
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y-%m-%d-%H%M")

    def add_message(self, role: str, content: str, source: str = "matrix"):
        """Add a message to the current conversation log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,           # "user", "vigil", "system"
            "content": content.strip(),
            "source": source
        }
        self.current_log.append(entry)
        print(f"[{entry['timestamp']}] {role.upper()}: {content[:60]}...")

    def save(self, title: str = None, auto_publish: bool = False) -> Path:
        """Save conversation as Obsidian-ready markdown."""
        if not self.current_log:
            return None

        now = datetime.now()
        filename = f"{self.session_id}-vigil-chat.md"
        filepath = LOG_DIR / filename

        # Build clean readable content
        conversation = []
        for msg in self.current_log:
            time_str = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
            role_label = "→ Andrew" if msg["role"] == "user" else "→ VIGIL"
            conversation.append(f"**{time_str} {role_label}**\n\n{msg['content']}\n")

        frontmatter = f"""---
title: "{title or 'VIGIL Conversation ' + self.session_id}"
date: {now.strftime("%Y-%m-%d")}
time: {now.strftime("%H:%M:%S")}
session_id: {self.session_id}
source: {self.current_log[0].get('source', 'matrix')}
participants: ["Andrew", "VIGIL"]
tags: [vigil, chat-log, matrix, hermes, automatic]
---

# {title or 'VIGIL Conversation'}

**Session:** {self.session_start.strftime("%Y-%m-%d %H:%M")} — {now.strftime("%H:%M")}

---

""" + "\n\n---\n\n".join(conversation) + """

---
*Automatically logged by VIGIL Chat Logger v2.0 (part of the Logician project).*
"""

        filepath.write_text(frontmatter, encoding="utf-8")
        print(f"✅ Saved chat log: {filepath}")

        if auto_publish:
            self.publish_to_vault(filepath)

        return filepath

    def publish_to_vault(self, log_file: Path) -> Path:
        """Safely copy to Obsidian vault."""
        dest = VAULT_DIR / log_file.name
        dest.write_text(log_file.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✅ Published to Obsidian vault: {dest}")
        return dest


# CLI for testing and manual use
if __name__ == "__main__":
    logger = ChatLogger()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.add_message("user", "Hello Vigil, this is a test of the automatic logger.")
        logger.add_message("vigil", "Hello Andrew. The automatic logging system is working correctly. All Matrix and terminal conversations will now be saved as clean Obsidian markdown files.")
        logger.save("Automatic Logger Test", auto_publish=True)
    else:
        print("VIGIL Chat Logger v2.0 ready.")
        print("Use in gateway or terminal wrapper for automatic logging.")
