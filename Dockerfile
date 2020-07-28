FROM ubuntu:18.04

# -- Configuration variables --
# tzdata
ARG region=Europe
ARG city=Copenhagen
# Django 
ARG DJANGO_PASSWORD=Passw0rd123
ARG DJANGO_USER=djangoadmin
ARG DJANGO_EMAIL=admin@localhost
# MPI cores
ARG MPI=1

# Get required commands for script
RUN apt-get update \
    && apt-get install -y adwaita-icon-theme git

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y keyboard-configuration

# Install and configure tzdata for bootstrap script
RUN ln -fs /usr/share/zoneinfo/${region}/${city} /etc/localtime \
    && apt-get install -y tzdata

RUN apt-get install -y net-tools iproute2 sudo zip unzip cron curl lsof

# Packages for bootstrapping an McWeb instance
RUN apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev python-virtualenv makepasswd nginx php-fpm php-mysql php-xml php-curl php-zip php-gd php-mbstring php-xmlrpc php-soap php-intl php-ldap build-essential

RUN apt-get install -y --fix-missing openssh-server

# Add nonfree and contrib repo
RUN sed -i.bak s/main/main\ contrib\ non-free/g /etc/apt/sources.list \
    && apt-get update

# Add mccode repo
RUN cd /etc/apt/sources.list.d/ \
    && wget http://packages.mccode.org/debian/mccode.list \
    && apt-get update

# Base packages for McCode + MPI
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/a/adwaita-icon-theme/adwaita-icon-theme_3.28.0-1ubuntu1_all.deb
RUN apt-get -y install -y mcstas-suite-perl mcstas-suite-python mcxtrace-suite-perl mcxtrace-suite-python openmpi-bin libopenmpi-dev

# Ensure we use mcdoc.pl rather than python version
RUN ln -sf /usr/share/mcstas/2.6/bin/mcdoc.pl /usr/bin/mcdoc

# Ensure mcplot.pl uses "proper" PGPLOT rather than GIZA
RUN cd /usr/lib/x86_64-linux-gnu \
    && sudo ln -sf ../libpgplot.so libpgplot.so.0 \
    && sudo ln -sf ../libcpgplot.so libcpgplot.so.0

# Remove stop apache2 from being default webserver
RUN update-rc.d apache2 remove

# Get local copy of McWeb repo. This is anticipating being run from McWeb dir
RUN mkdir -p /srv/mcweb/McWeb
COPY . /srv/mcweb/McWeb

RUN sudo chown -R www-data:www-data /srv/mcweb /var/www/

# Bootstrap McWeb via sudo / git
RUN cd /srv/mcweb \
    && sudo -H -u www-data virtualenv mcvenv \
    && sudo -u www-data cp mcvenv/bin/activate mcvenv_finishup \
    && echo pip install -I pyparsing ply numpy >> mcvenv_finishup \
    && echo pip install -I Django==1.8.2 django-auth-ldap==1.2.7 simplejson python-ldap >> mcvenv_finishup \
    && echo pip install uwsgi >> mcvenv_finishup \
    && sudo -H -u www-data bash mcvenv_finishup

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3 get-pip.py \
    && python3 -m pip install --ignore-installed jmespath==0.9.4 cryptography==2.8 six==1.14.0 corc \
    && rm get-pip.py

ENV LANG=C.UTF-8

RUN cd /srv/mcweb \
    && ln -sf /srv/mcweb/McWeb/scripts/uwsgi_mcweb /etc/init.d/uwsgi_mcweb \
    && update-rc.d uwsgi_mcweb defaults

ENV IPADDR `ip addr show | grep inet\ | cut -f 2 -d\t | cut -f 1 -d/ |grep -v 127 | sed "s/\ //g"`
ENV SERVERNAME `hostname`
ENV UPLOADPW $DJANGO_PASSWORD
ENV MPICORES $MPI

# Allow www-data to restart uwsgi and claim ownership of files
RUN echo >> /etc/sudoers \
    && echo "# Allow www-data to restart uwsgi_mcweb service" >> /etc/sudoers \
    && echo "www-data ALL = NOPASSWD: /etc/init.d/uwsgi_mcweb" >> /etc/sudoers \
    && echo "www-data ALL = NOPASSWD: /bin/chown" >> /etc/sudoers

  # Last setup of uwsgi etc
RUN echo Resuming setup... \
    && sed "s/dc=risoe,dc=dk/${LDAPDOMAIN}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py.in > /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/@LDAP_PW@/${LDAP_PASS}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/@IPADDR@/127.0.0.1/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/@SERVERNAME@/localhost/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/@UPLOADPW@/${UPLOADPW}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/@MPICORES@/${MPICORES}/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/'django_auth_ldap/\#'django_auth_ldap/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/\#'django.contrib.auth/'django.contrib.auth/g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/DEBUG = True/DEBUG = False/" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py \
    && sed -i "s/-dev//g" /srv/mcweb/McWeb/mcsimrunner/mcweb/settings.py

# Simple, static "admin" landing page
RUN cd /srv/mcweb \
    && sudo -u www-data mkdir landing \
    && sed "s/@HOSTNAME@/${SERVERNAME}/g" McWeb/landingpage/landingpage.in.html > landing/index.html \
    && chown www-data:www-data landing/index.html

RUN cd /srv/mcweb \
    && sudo -u www-data cp mcvenv/bin/activate McWeb_finishup \
    && echo cd McWeb/mcsimrunner/ >> McWeb_finishup \
    && echo python manage.py migrate >> McWeb_finishup \
    && echo python manage.py collect_instr >> McWeb_finishup \
    && echo "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$DJANGO_USER', '$DJANGO_EMAIL', '$DJANGO_PASSWORD')\" | python manage.py shell" >> McWeb_finishup \
    && echo echo $DJANGO_PASSWORD >> McWeb_finishup \
    && echo echo >> McWeb_finishup \
    && echo echo Essential setup done, here is a summary: >> McWeb_finishup \
    && echo echo >> McWeb_finishup \
    && echo echo Django setup: >> McWeb_finishup \
    && echo echo username: $DJANGO_USER >> McWeb_finishup \
    && echo echo password: $DJANGO_PASS >> McWeb_finishup \
    && echo echo email-adress: admin@localhost >> McWeb_finishup \
    && echo echo Django upload pass: $UPLOADPASS >> McWeb_finishup \
    && echo echo >> McWeb_finishup \
    && echo crontab /srv/mcweb/McWeb/scripts/cronjobs.txt >> McWeb_finishup

RUN cd /srv/mcweb \
    && sudo -H -u www-data bash McWeb_finishup

# overwrite nginx defaults
COPY nginx/mcweb.conf /srv/mcweb/McWeb/scripts/nginx-default
RUN cat /srv/mcweb/McWeb/scripts/nginx-default > /etc/nginx/sites-enabled/default

# Copy in docker entry script as it'll have been deleted my the pull from McWeb-stable
COPY scripts/docker-entry.sh /srv/mcweb/McWeb/scripts/docker-entry.sh

# Used for development. Can be removed from finished project
RUN apt-get -y install locate nano iputils-ping dnsutils \
    && updatedb

EXPOSE 80 443

CMD ["bash", "/srv/mcweb/McWeb/scripts/docker-entry.sh"]
