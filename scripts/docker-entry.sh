#!/bin/bash

/etc/init.d/uwsgi_mcweb start
service nginx restart
service cron restart
# Needed to update shell for oci-cli
service uwsgi_mcweb restart

# Take ownership of mounted directories
chown -R www-data:www-data /srv/mcweb/McWeb/mcsimrunner/sim /srv/mcweb/McWeb/mcsimrunner/static/data

# Collect initial instruments
sudo -u www-data /srv/mcweb/McWeb/scripts/update_instr.sh

# Hack to keep this image running indefinitely
tail -f /dev/null