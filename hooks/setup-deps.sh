#!/bin/bash

CACHED="${CLAUDE_PLUGIN_DATA}/pyproject.toml"
CURRENT="${CLAUDE_PLUGIN_ROOT}/pyproject.toml"

mkdir -p "${CLAUDE_PLUGIN_DATA}"

# Install/update dependencies when pyproject.toml changes
if ! diff -q "$CACHED" "$CURRENT" >/dev/null 2>&1; then
  echo "amelia: installing dependencies..."
  cd "${CLAUDE_PLUGIN_ROOT}" || exit 1

  if uv sync; then
    cp "$CURRENT" "$CACHED"
    echo "amelia: dependencies installed"
  else
    echo "amelia: failed to install dependencies"
    exit 1
  fi
fi

# Create starter config if it doesn't exist
if [ ! -d "$HOME/.amelia" ]; then
  mkdir -p "$HOME/.amelia"
fi

if [ ! -f "$HOME/.amelia/config.md" ]; then
  cp "${CLAUDE_PLUGIN_ROOT}/config.default.md" "$HOME/.amelia/config.md"
  echo "amelia: created ~/.amelia/config.md — edit it to set your preferences"
fi

# Check for API keys — output instruction to Claude if missing
if [ ! -f "$HOME/.amelia/.env" ]; then
  echo "AMELIA SETUP REQUIRED: ~/.amelia/.env does not exist. Before running any travel searches, you MUST ask the user for their API keys and create the file. Ask for: SEATS_AERO_API_KEY (required — from seats.aero Pro plan) and SERPAPI_KEY (optional — for hotel search fallback). Write them to ~/.amelia/.env. Alternatively, run /amelia:setup which includes key collection."
fi

# Check for missing permissions — tell Claude to ask user
SETTINGS="$HOME/.claude/settings.json"
REQUIRED_PERMS=(
  'Bash(uv run:*)'
  'Bash(mkdir -p ~/.amelia/*)'
  'Read(~/.amelia/**)'
  'Read(~/.claude/plugins/cache/00derek-amelia/**)'
  'Edit(~/.amelia/**)'
  'Write(~/.amelia/**)'
)

MISSING=""
if [ -f "$SETTINGS" ] && command -v jq >/dev/null 2>&1; then
  for PERM in "${REQUIRED_PERMS[@]}"; do
    if ! jq -e --arg p "$PERM" '(.permissions.allow // []) | index($p)' "$SETTINGS" >/dev/null 2>&1; then
      MISSING="$MISSING  - $PERM"$'\n'
    fi
  done
elif [ ! -f "$SETTINGS" ]; then
  for PERM in "${REQUIRED_PERMS[@]}"; do
    MISSING="$MISSING  - $PERM"$'\n'
  done
fi

if [ -n "$MISSING" ]; then
  echo "AMELIA PERMISSIONS: The following permissions are missing from ~/.claude/settings.json and are needed for amelia to work without interruptions (subagents, file I/O, trip folders):"
  echo "$MISSING"
  echo "Use AskUserQuestion to ask the user: 'Amelia needs to add these permissions to ~/.claude/settings.json for friction-free searches. OK to add them?' If yes, read the file, add the missing entries to permissions.allow using jq, and write it back."
fi
