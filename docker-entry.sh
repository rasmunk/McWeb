#!/bin/bash

/etc/init.d/uwsgi_mcweb start
service nginx restart
service cron restart

# Hack to keep this running indefinetly
tail -f /dev/null