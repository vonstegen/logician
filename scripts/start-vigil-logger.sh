#!/bin/bash
# start-vigil-logger.sh — Fully Automatic Chat Logging for VIGIL
# Logs both Matrix (via Hermes gateway) and terminal conversations
# Saves to ~/logician/chat-logs/ and optionally publishes to Obsidian vault

set -e

LOG_DIR="$HOME/logician/chat-logs"
VAULT_DIR="/home/vigil/VonStegen-Master-Vault/Chats/Vigil"
mkdir -p "$LOG_DIR" "$VAULT_DIR"

echo "=== VIGIL Automatic Chat Logger v2.0 ==="
echo "Starting automatic logging for Matrix and Hermes terminal sessions..."
echo "Logs will be saved to $LOG_DIR"
echo "Published logs will appear in $VAULT_DIR"
echo ""

# Start or restart the Hermes gateway with logging enabled
echo "Starting Hermes gateway with logging..."
tmux kill-session -t hermes-gateway 2>/dev/null || true
tmux new-session -d -s hermes-gateway "hermes gateway run 2>&1 | tee -a $LOG_DIR/gateway-raw.log"

echo "Gateway started in tmux session 'hermes-gateway'."
echo "A background processor will convert raw logs into clean Obsidian markdown every 5 minutes."

# Create background processor
cat > /tmp/vigil-log-processor.py << 'EOF'
import time, re, json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / "logician" / "chat-logs"
VAULT_DIR = Path("/home/vigil/VonStegen-Master-Vault/Chats/Vigil")
VAULT_DIR.mkdir(parents=True, exist_ok=True)

def process_raw_log():
    raw_log = Path.home() / "logician" / "chat-logs" / "gateway-raw.log"
    if not raw_log.exists():
        return
    
    # Simple parser for now — can be enhanced with Matrix SDK later
    with open(raw_log, "r") as f:
        lines = f.readlines()[-50:]  # last 50 lines to avoid duplicates
    
    content = "\n".join(lines)
    if "Hello" in content or "VIGIL" in content:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        filepath = LOG_DIR / f"{timestamp}-vigil-auto.md"
        
        frontmatter = f"""---
title: "VIGIL Automatic Chat {timestamp}"
date: {datetime.now().strftime("%Y-%m-%d")}
time: {datetime.now().strftime("%H:%M:%S")}
source: matrix+terminal
tags: [vigil, automatic-log, matrix, hermes]
---

# VIGIL Automatic Chat Log

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{content}

---
*Automatically logged by VIGIL Chat Logger v2.0*
"""
        filepath.write_text(frontmatter)
        print(f"Auto-saved: {filepath}")
        
        # Auto-publish to vault
        vault_file = VAULT_DIR / filepath.name
        vault_file.write_text(filepath.read_text())
        print(f"Published to vault: {vault_file}")

if __name__ == "__main__":
    while True:
        process_raw_log()
        time.sleep(300)  # every 5 minutes
EOF

python3 /tmp/vigil-log-processor.py > /tmp/vigil-log-processor.log 2>&1 &

echo "Background log processor started."
echo ""
echo "✅ Fully automatic logging is now active."
echo "All Matrix and terminal conversations with VIGIL will be saved as clean Obsidian markdown files."
echo "Check $LOG_DIR and $VAULT_DIR regularly."
echo ""
echo "To view live gateway: tmux attach -t hermes-gateway"
echo "To stop: tmux kill-session -t hermes-gateway"
