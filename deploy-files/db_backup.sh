#!/bin/bash
TIMESTAMP=`date "+%Y%m%d%H%M%S"`
DB_BACKUP_NAME=${TIMESTAMP}_russ2018.psql.dump 
echo "Making DB backup to ${DB_BACKUP_NAME}.."
PGPASSWORD="russ2018" pg_dump -v -Fc -h 127.0.0.1 -U russ2018 -d russ2018 > ./$DB_BACKUP_NAME
echo "Making DB backup..DONE"

