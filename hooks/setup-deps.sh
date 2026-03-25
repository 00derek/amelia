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

# Nudge user to run setup if .env is missing
if [ ! -f "$HOME/.amelia/.env" ]; then
  echo "amelia: run /amelia:setup to configure API keys"
fi
