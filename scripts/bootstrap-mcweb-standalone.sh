#!/bin/sh

STARTDIR=`pwd`
# Basic infrastructure
echo Starting to setup basic infrastructure
apt-get -y
echo installing net tools
apt-get -y install net-tools
echo installing iproute2
apt-get -y install iproute2
echo installing sudo
apt-get -y install sudo
echo installing openssh
apt-get -y install openssh-server
echo installing xbase
apt-get -y install xbase-clients
echo installing zio
apt-get -y install zip
echo installing unzip
apt-get -y install unzip
echo installing cron
apt-get -y install cron
echo installing curls
apt-get -y install curl
echo installing lsof
apt-get -y install lsof

# Add nonfree and contrib repo
echo Adding nor free and contrib repo
sed -i.bak s/main/main\ contrib\ non-free/g /etc/apt/sources.list
echo UPDATING APT GET
apt-get update

# Add mccode repo
echo adding MCCODE REPO
cd /etc/apt/sources.list.d/
echo REMOVING MCCODE.LIST
rm mccode.list
echo  GETTING NEW LIST
wget http://packages.mccode.org/debian/mccode.list
echo UPDATING APT GET
apt-get update
echo MOVING TO STARTDIR
cd $STARTDIR

# Base packages for McCode + MPI
echo INSTALLING MCSTAS IN PERL
apt-get -y install mcstas-suite-perl
echo INSTALLING MCSTAS IN PYTHON
apt-get -y install mcstas-suite-python
echo INSTALLING MCXTRACE IN PERL
apt-get -y install mcxtrace-suite-perl
echo INSTALLING MCXTRACE IN PYTHON
apt-get -y install mcxtrace-suite-python
echo INSTALLING OPEN MPI
apt-get -y install openmpi-bin
echo INSTALLING LIB OPEN MPI
apt-get -y install libopenmpi-dev
# Ensure we use mcdoc.pl rather than python version
echo USING MCDOC.PL
ln -sf /usr/share/mcstas/2.6/bin/mcdoc.pl /usr/bin/mcdoc
# Ensure mcplot.pl uses "proper" PGPLOT rather than GIZA
echo USING PROPER PGPLOT
cd /usr/lib/x86_64-linux-gnu
echo FIRST LINKING
sudo ln -sf ../libpgplot.so libpgplot.so.0
echo SECOND LINKING
sudo ln -sf ../libcpgplot.so libcpgplot.so.0
echo REVERTING TO START DIR
cd $STARTDIR

# Remove stop apache2 from being default webserver
echo UPDATING APACHE
update-rc.d apache2 remove
echo REMOVING APACHE
service apache2 stop

# Packages for bootstrapping an McWeb instance
echo INSTALLING GIT
apt-get -y install git
echo INSTALLING LIBSAS
apt-get -y install libsasl2-dev
echo INSTALLING PYTHON DEV
apt-get -y install python-dev
echo INSTALLING LIBLDAP
apt-get -y install libldap2-dev
echo INSTALLING LIBSAL
apt-get -y install libssl-dev
echo INSTALLING PYTON VIRTENV
apt-get -y install python-virtualenv
echo INSTALLING MAKEPASSWD
apt-get -y install makepasswd
echo INSTALLING NGINX
apt-get -y install nginx
echo INSTALLING PHP FPM
apt-get -y install php-fpm
echo INSTALLING PIP MYSQL
apt-get -y install php-mysql
echo INSTALLING PHP XML
apt-get -y install php-xml
echo INSTALLING PHP CURL
apt-get -y install php-curl
echo INSTALLING PHP ZIP
apt-get -y install php-zip
echo INSTALLING PHP GD
apt-get -y install php-gd
echo INSTALLING PHP MBSTRING
apt-get -y install php-mbstring
echo INSTALLING PHP XMLRPC
apt-get -y install php-xmlrpc
echo INSTALLING PHP SOAP
apt-get -y install php-soap
echo INSTALLING PHP INTL
apt-get -y install php-intl
echo INSTALLING PHP LDAP
apt-get -y install php-ldap

echo REMOVING SRV MCWEB
rm -rf /srv/mcweb
echo MAKING SRV MCWEB
mkdir /srv/mcweb
echo OWNING SRV MCWEB
sudo chown -R www-data:www-data /srv/mcweb /var/www/

# Bootstrap McWeb via sudo / git
echo MOVING TO SRV MCWEB
cd /srv/mcweb
echo VIRTUAL ENVING
sudo -H -u www-data virtualenv mcvenv
echo COPYING VITRUALENV ACTIVATION
sudo -u www-data cp mcvenv/bin/activate mcvenv_finishup
echo PIP INSTALLING DJANGO TO MCVENV
echo pip install -I Django==1.8.2 django-auth-ldap==1.2.7 simplejson python-ldap >> mcvenv_finishup
#echo pip install -I django-auth-ldap==1.2.7 >> mcvenv_finishup
echo PIP INSTALLING UWSGI TO MCVENV
echo pip install uwsgi  >> mcvenv_finishup
echo MAYBE STARTING MCVENV
sudo -H -u www-data  bash mcvenv_finishup

echo CLONING GIT REPO
sudo -H -u www-data  git clone --single-branch --branch patch https://github.com/rasmunk/McWeb

# Pick and pull the STABLE branch
echo MOVING INTO MCWEB
cd McWeb
echo CHEKING OUT STABLE
sudo -H -u www-data  git checkout MCWEB_STABLE_2.0
echo PULLING
sudo -H -u www-data  git pull

echo MOVING INTO SRV
cd /srv/mcweb
echo LINKING UWSGI
ln -sf /srv/mcweb/McWeb/scripts/uwsgi_mcweb /etc/init.d/uwsgi_mcweb
echo UPDATING UWSGI
update-rc.d uwsgi_mcweb defaults

echo SHOWING OFF IP
IPADDR=`ip addr show | grep inet\ | cut -f 2 -d\t | cut -f 1 -d/ |grep -v 127 | sed "s/\ //g"`
SERVERNAME=`hostname`
echo EXPORTING IP
export IPADDR
export SERVERNAME

echo GETTING DJANGO PW
echo -n Please enter your Django upload password and press [ENTER]:
read UPLOADPW
export UPLOADPW

echo GETING MPI CORES
echo -n Please enter desired simulator MPI cores pr. sim job press [ENTER]:
read MPICORES
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
sudo -u www-data cp mcvenv/bin/activate McWeb_finishup
echo cd McWeb/mcsimrunner/ >> McWeb_finishup
echo python manage.py migrate >> McWeb_finishup
echo python manage.py collect_instr >>  McWeb_finishup
echo echo Please assist Django in creation of your djangoadmin user: >>  McWeb_finishup
echo python manage.py createsuperuser --username=djangoadmin --email=admin@localhost >>  McWeb_finishup >>  McWeb_finishup
echo echo -n Please enter your Django admin user pass again and press \[ENTER\]: >>  McWeb_finishup
echo read DJANGO_PASS >>  McWeb_finishup
echo echo >>  McWeb_finishup
echo echo Essential setup done, here is a summary: >>  McWeb_finishup
echo echo >>  McWeb_finishup
echo echo Django setup: >>  McWeb_finishup
echo echo username: djangoadmin >>  McWeb_finishup
echo echo password: \$DJANGO_PASS >>  McWeb_finishup
echo echo email-adress: admin@localhost >>  McWeb_finishup
echo echo Django upload pass: $UPLOADPASS >>  McWeb_finishup
echo echo >>  McWeb_finishup 
echo crontab /srv/mcweb/McWeb/scripts/cronjobs.txt >> McWeb_finishup 

sudo -H -u www-data  bash McWeb_finishup
/etc/init.d/uwsgi_mcweb start

cat /srv/mcweb/McWeb/scripts/nginx-default > /etc/nginx/sites-enabled/default
service nginx restart


