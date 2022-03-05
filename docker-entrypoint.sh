#!/bin/sh

set -e

. /venv/bin/activate

exec python /app/src/web.py
