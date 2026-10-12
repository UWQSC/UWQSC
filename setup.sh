#!/bin/bash

# Python setup (installs Python 3.12 if needed and creates .venv)
uv sync

# Git hooks setup
cp bin/commit-msg.sh .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
