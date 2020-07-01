#!/bin/bash

/etc/init.d/uwsgi_mcweb start
service nginx restart
service cron restart

## Collect initial instruments
sudo -u www-data /srv/mcweb/McWeb/scripts/update_instr.sh

# Hack to keep this image running indefinitely
tail -f /dev/null