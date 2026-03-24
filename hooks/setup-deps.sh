#!/bin/bash

CACHED="${CLAUDE_PLUGIN_DATA}/pyproject.toml"
CURRENT="${CLAUDE_PLUGIN_ROOT}/pyproject.toml"

mkdir -p "${CLAUDE_PLUGIN_DATA}"

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

# Prompt user to create .env if it doesn't exist
if [ ! -f "$HOME/.amelia/.env" ]; then
  echo "amelia: no API keys found. Create ~/.amelia/.env with your keys:"
  echo "  mkdir -p ~/.amelia"
  echo "  echo 'SEATS_AERO_API_KEY=your-key' >> ~/.amelia/.env"
  echo "  echo 'SERPAPI_KEY=your-key' >> ~/.amelia/.env"
fi
