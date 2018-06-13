#!/bin/bash
source /home/russ/venv-russ2018/bin/activate
exec /home/russ/venv-russ2018/bin/celery --purge worker -l debug --config Russia2018Backend.celery_conf


