#!/bin/bash

# Python setup
python3.9 -m venv venv 
source venv/bin/activate 
pip install --upgrade pip
pip install -r requirements.txt

# Git hooks setup 
scp bin/commit-msg.sh .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
