#!/bin/bash

MARKER="${CLAUDE_PLUGIN_DATA}/uv-synced"

if [ ! -f "$MARKER" ]; then
  echo "Installing amelia dependencies..."
  cd "${CLAUDE_PLUGIN_ROOT}" || exit 1

  if uv sync; then
    mkdir -p "${CLAUDE_PLUGIN_DATA}"
    touch "$MARKER"
    echo "amelia: dependencies installed"
  else
    echo "amelia: failed to install dependencies"
    exit 1
  fi
fi
