#!/bin/bash
# Auto-start wrapper for VIGIL Chat Logger
# Runs at boot and ensures logger + gateway are active

LOG_DIR="$HOME/logician/chat-logs"
mkdir -p "$LOG_DIR"

echo "[$(date)] VIGIL Auto-Start Logger activated" >> $LOG_DIR/boot.log

# Kill any old sessions
tmux kill-session -t hermes-gateway 2>/dev/null || true

# Start gateway with full logging
tmux new-session -d -s hermes-gateway "hermes gateway run 2>&1 | tee -a $LOG_DIR/gateway-raw.log"

# Start the log processor in background
python3 $HOME/logician/scripts/vigil-log-processor.py >> $LOG_DIR/processor.log 2>&1 &

echo "[$(date)] Gateway and logger started successfully" >> $LOG_DIR/boot.log
