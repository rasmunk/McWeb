#!/bin/sh

STARTDIR=`pwd`

# Defaults
# Django
DJANGO_PASSWORD="Passw0rd123"
DJANGO_USER="djangoadmin"
DJANGO_EMAIL="admin@localhost"
# Number of MPI cores
MPI=1

print_usage() {
	print "-p for new DJANGO Password"
	print "-u for new DJANGO user"
	print "-e for new DJANGO email"
}

while getopts 'hp:u:e:m:' flag; do
	case ${flag} in
		p) DJANGO_PASSWORD=${OPTARG} ;;
		u) DJANGO_USER=${OPTARG} ;;
		e) DJANGO_EMAIL=${OPTARG} ;;
		m) MPI=${OPTARG} ;;
		h) print_usage
		  exit 1 ;;
	esac
done

# Add nonfree and contrib repo
sed -i.bak s/main/main\ contrib\ non-free/g /etc/apt/sources.list
apt-get update

# Add mccode repo
cd /etc/apt/sources.list.d/
wget http://packages.mccode.org/debian/mccode.list
apt-get update
cd $STARTDIR

# Base packages for McCode + MPI
apt-get -y install -y mcstas-suite-perl
apt-get -y install -y mcstas-suite-python
apt-get -y install -y mcxtrace-suite-perl
apt-get -y install -y mcxtrace-suite-python
apt-get -y install -y openmpi-bin
apt-get -y install -y libopenmpi-dev
# Ensure we use mcdoc.pl rather than python version
ln -sf /usr/share/mcstas/2.6/bin/mcdoc.pl /usr/bin/mcdoc
# Ensure mcplot.pl uses "proper" PGPLOT rather than GIZA
cd /usr/lib/x86_64-linux-gnu
sudo ln -sf ../libpgplot.so libpgplot.so.0
sudo ln -sf ../libcpgplot.so libcpgplot.so.0
cd $STARTDIR

# Remove stop apache2 from being default webserver
update-rc.d apache2 remove
service apache2 stop

rm -rf /srv/mcweb
mkdir /srv/mcweb
sudo chown -R www-data:www-data /srv/mcweb /var/www/

# Bootstrap McWeb via sudo / git
cd /srv/mcweb
sudo -H -u www-data virtualenv mcvenv
sudo -u www-data cp mcvenv/bin/activate mcvenv_finishup
echo pip install -I Django==1.8.2 django-auth-ldap==1.2.7 simplejson python-ldap >> mcvenv_finishup
#echo pip install -I django-auth-ldap==1.2.7 >> mcvenv_finishup
echo pip install uwsgi  >> mcvenv_finishup
sudo -H -u www-data  bash mcvenv_finishup

# sudo -H -u www-data  git clone https://github.com/rasmunk/McWeb

# Pick and pull the STABLE branch
cd McWeb
sudo -H -u www-data  git checkout MCWEB_STABLE_2.0
sudo -H -u www-data  git pull

cd /srv/mcweb
ln -sf /srv/mcweb/McWeb/scripts/uwsgi_mcweb /etc/init.d/uwsgi_mcweb
update-rc.d uwsgi_mcweb defaults

IPADDR=`ip addr show | grep inet\ | cut -f 2 -d\t | cut -f 1 -d/ |grep -v 127 | sed "s/\ //g"`
SERVERNAME=`hostname`
export IPADDR
export SERVERNAME

# echo -n Please enter your Django upload password and press [ENTER]:
# read UPLOADPW
UPLOADPW=$DJANGO_PASSWORD
export UPLOADPW

# echo -n Please enter desired simulator MPI cores pr. sim job press [ENTER]:
# read MPICORES
MPICORES=$MPI
export MPICORES

# Allow www-data to restart uwsgi
echo >> /etc/sudoers
echo "# Allow www-data to restart uwsgi_mcweb service" >> /etc/sudoers
echo "www-data ALL = NOPASSWD: /etc/init.d/uwsgi_mcweb" >> /etc/sudoers

# Last setup of uwsgi etc
echo Resuming setup...
sed "s/dc=risoe,dc=dk/${LDAPDOMAIN}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py.in > /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/@LDAP_PW@/${LDAP_PASS}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py 
sed -i "s/@IPADDR@/127.0.0.1/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py 
sed -i "s/@SERVERNAME@/localhost/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/@UPLOADPW@/${UPLOADPW}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/@MPICORES@/${MPICORES}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/'django_auth_ldap/\#'django_auth_ldap/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/\#'django.contrib.auth/'django.contrib.auth/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/DEBUG = True/DEBUG = False/" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py
sed -i "s/-dev//g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py

# Simple, static "admin" landing page
cd /srv/mcweb
sudo -u www-data mkdir landing
sed "s/@HOSTNAME@/${SERVERNAME}/g" McWeb/landingpage/landingpage.in.html > landing/index.html
chown www-data:www-data landing/index.html

cd /srv/mcweb
sudo -u www-data mkdir McWeb/mcsimrunner/sim/intro-ns
sudo -u www-data cp /usr/share/mcstas/2.6/examples/templateSANS.instr /srv/mcweb/McWeb/mcsimrunner/sim/intro-ns/SANSsimple.instr
sudo -u www-data cp /usr/share/mcstas/2.6/examples/Tomography.instr /srv/mcweb/McWeb/mcsimrunner/sim/intro-ns/
# This can be removed for a significant speedup in the build process
# sudo -u www-data cp -a /usr/share/mcstas/2.6/examples/*.instr /srv/mcweb/McWeb/mcsimrunner/sim/intro-ns/
sudo -u www-data cp mcvenv/bin/activate McWeb_finishup
echo cd McWeb/mcsimrunner/ >> McWeb_finishup
echo python manage.py migrate >> McWeb_finishup
echo python manage.py collect_instr >>  McWeb_finishup

echo "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$DJANGO_USER', '$DJANGO_EMAIL', '$DJANGO_PASSWORD')\" | python manage.py shell" >> McWeb_finishup

echo echo $DJANGO_PASSWORD >> McWeb_finishup
echo echo >>  McWeb_finishup
echo echo Essential setup done, here is a summary: >>  McWeb_finishup
echo echo >>  McWeb_finishup
echo echo Django setup: >>  McWeb_finishup
echo echo username: $DJANGO_USER >>  McWeb_finishup
echo echo password: $DJANGO_PASS >>  McWeb_finishup
echo echo email-adress: admin@localhost >>  McWeb_finishup
echo echo Django upload pass: $UPLOADPASS >>  McWeb_finishup
echo echo >>  McWeb_finishup
echo crontab /srv/mcweb/McWeb/scripts/cronjobs.txt >> McWeb_finishup

sudo -H -u www-data  bash McWeb_finishup
# /etc/init.d/uwsgi_mcweb start

cat /srv/mcweb/McWeb/scripts/nginx-default > /etc/nginx/sites-enabled/default
# service nginx restart

#cd
#echo 'script completed, possibly' >> feedback.txt
