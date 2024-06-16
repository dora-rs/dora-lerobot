#!/usr/bin/env bash

# Path to your virtual environment
VENV_PATH="venv"

# Activate the virtual environment
source "${VENV_PATH}/bin/activate"

# Run Python
python "$@"