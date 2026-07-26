#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="aap-chatops"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session '$SESSION_NAME' is already running. Attaching..."
else
    echo "Starting new session '$SESSION_NAME'..."
    tmux new-session -d -s "$SESSION_NAME" -c "$REPO_DIR" "uv run python -m aap_chatops.main"
fi

tmux attach -t "$SESSION_NAME"
