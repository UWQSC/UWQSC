#!/bin/bash

RED='\033[0;31m' 
commitMessageFile="$1"
commitMessageRegex="^topic/#[0-9]*$"
commitMessageError="Your commit message should have GitHub Actions number on a new line inside it.

Correct commit message:
<<commit message starts>>
Unit Tests for AlgoML
topic/#100
...
<<commit message ends>>

Note: Use 'git commit' instead of 'git commit -m' to open up an editor."

if ! grep -q "$commitMessageRegex" "$commitMessageFile"; then
  echo -e "${RED}$commitMessageError" >&2
  exit 1
fi

exit 0
