#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
export JUPYTER_RUNTIME_DIR="$PWD/.cache/jupyter/runtime"
export JUPYTER_CONFIG_DIR="$PWD/.cache/jupyter/config"
export JUPYTER_DATA_DIR="$PWD/.venv/share/jupyter"
export IPYTHONDIR="$PWD/.cache/ipython"
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_CONFIG_DIR" "$IPYTHONDIR" "$MPLCONFIGDIR"
exec ./.venv/bin/python -m jupyterlab --ServerApp.ip=127.0.0.1
