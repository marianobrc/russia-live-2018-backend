#!/bin/bash
# IMPORTANT: This file must be placed next to manage.py
source /home/russ/venv-russ2018/bin/activate
exec /home/russ/venv-russ2018/bin/gunicorn -c /home/russ/russia-live-2018-backend/Russia2018Backend/gunicorn.conf.py chekin.wsgi:application
