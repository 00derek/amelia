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

# Seed required permissions directly into user settings
SETTINGS="$HOME/.claude/settings.json"
REQUIRED_PERMS=(
  'Bash(uv run:*)'
  'Read(~/.amelia/**)'
  'Edit(~/.amelia/**)'
  'Write(~/.amelia/**)'
)

if command -v jq >/dev/null 2>&1; then
  if [ ! -f "$SETTINGS" ]; then
    printf '%s\n' "${REQUIRED_PERMS[@]}" | jq -R . | jq -s '{permissions: {allow: .}}' > "$SETTINGS"
    echo "amelia: created ~/.claude/settings.json with required permissions"
  else
    for PERM in "${REQUIRED_PERMS[@]}"; do
      if ! jq -e --arg p "$PERM" '(.permissions.allow // []) | index($p)' "$SETTINGS" >/dev/null 2>&1; then
        TMP=$(mktemp)
        jq --arg p "$PERM" '.permissions.allow = ((.permissions.allow // []) + [$p])' "$SETTINGS" > "$TMP" && mv "$TMP" "$SETTINGS"
      fi
    done
    echo "amelia: permissions configured"
  fi
else
  echo "AMELIA: jq not found — install it (brew install jq) or manually add these to ~/.claude/settings.json permissions.allow: Bash(uv run:*), Read(~/.amelia/**), Edit(~/.amelia/**), Write(~/.amelia/**)"
fi
