#!/bin/bash

/etc/init.d/uwsgi_mcweb start
service nginx restart
service cron restart

## Collect initial instruments
/srv/mcweb/McWeb/scripts/update_instr.sh > initial_update.log
#source /srv/mcweb/mcvenv/bin/activate
#cd /srv/mcweb/McWeb/mcsimrunner/
#sudo -u www-data python manage.py collect_instr > /srv/mcweb/McWeb/mcsimrunner/static/compile_status.html
#deactivate

# Hack to keep this running indefinitely
tail -f /dev/null