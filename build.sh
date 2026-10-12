#!/usr/bin/env bash
# Script de construcción para Render. Falla ante cualquier error.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
