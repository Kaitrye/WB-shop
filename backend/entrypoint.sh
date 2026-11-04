#!/bin/sh
set -e

pdm run python manage.py migrate --noinput
exec "$@"