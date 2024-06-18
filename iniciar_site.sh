#!/bin/bash
export PYTHONPATH=/home/avant/fechaduraLabSV
exec authbind gunicorn -w 2 -b 0.0.0.0:80 app:app
