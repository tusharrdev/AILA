#!/usr/bin/env bash
# Remove any existing venv
rm -rf .venv
# Install globally
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --no-input
python3 manage.py migrate