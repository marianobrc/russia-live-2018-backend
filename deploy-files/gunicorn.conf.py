from __future__ import unicode_literals
# Important: Put this file next to wsgi file (usually project settings dir)
bind = "unix:/home/russ/russia-live-2018-backend/deploy-files/gunicorn.sock"
workers = 6
proc_name = "russ2018"
pid = "/home/russ/russia-live-2018-backend/deploy-files/gunicorn.pid"
accesslog = "/home/russ/russia-live-2018-backend/logs/gunicorn_access.log"
timeout = 3600
graceful_timeout = 30
limit_request_line = 0
