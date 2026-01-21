#!/usr/bin/env bash
# Don't use pip from venv, use system pip
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --no-input
python3 manage.py migratecls
