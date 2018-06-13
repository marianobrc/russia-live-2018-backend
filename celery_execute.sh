#!/bin/bash
source /home/chekin/venv-chekin/bin/activate
exec /home/chekin/venv-chekin/bin/celery --purge worker -l debug --config Russia2018Backend.celery_conf


