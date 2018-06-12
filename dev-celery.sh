#!/bin/bash
# Celery worker
# Requires to execute the virtualenvironment first

trap killgroup EXIT

killgroup(){
  echo killing...
  kill $(jobs -p)
}

#redis-server &
celery --purge worker -l debug --config Russia2018Backend.celery_conf &
wait
echo "done"