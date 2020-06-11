#!/bin/bash

/etc/init.d/uwsgi_mcweb start
service nginx restart
service cron restart

## Collect initial instruments
#cd /srv/mcweb/McWeb/mcsimrunner/
#python manage.py collect_instr > /srv/mcweb/McWeb/mcsimrunner/static/compile_status.html

# Hack to keep this running indefinitely
tail -f /dev/null