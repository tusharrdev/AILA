#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Add this line to ensure gunicorn is in the right place
pip install gunicorn