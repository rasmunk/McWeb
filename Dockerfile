FROM ubuntu:18.04

RUN set -e

# -- Configuration variables --
# tzdata
ARG region=Europe
ARG city=Copenhagen
# Django 
ARG DJANGO=Passw0rd123
# MPI cores
ARG MPI=1

# Get required commands for script
RUN apt-get update

RUN apt-get install -y git

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y keyboard-configuration

# Install and configure tzdata for bootstrap script
RUN ln -fs /usr/share/zoneinfo/${region}/${city} /etc/localtime \
    && apt-get install -y tzdata

RUN apt-get install -y net-tools
RUN apt-get install -y iproute2
RUN apt-get install -y sudo
RUN apt-get install -y zip
RUN apt-get install -y unzip
RUN apt-get install -y cron
RUN apt-get install -y curl
RUN apt-get install -y lsof

# Packages for bootstrapping an McWeb instance
RUN apt-get -y install libsasl2-dev
RUN apt-get -y install python-dev
RUN apt-get -y install libldap2-dev
RUN apt-get -y install libssl-dev
RUN apt-get -y install python-virtualenv
RUN apt-get -y install makepasswd
RUN apt-get -y install nginx
RUN apt-get -y install php-fpm
RUN apt-get -y install php-mysql
RUN apt-get -y install php-xml
RUN apt-get -y install php-curl
RUN apt-get -y install php-zip
RUN apt-get -y install php-gd
RUN apt-get -y install php-mbstring
RUN apt-get -y install php-xmlrpc
RUN apt-get -y install php-soap
RUN apt-get -y install php-intl
RUN apt-get -y install php-ldap

RUN apt-get install -y --fix-missing openssh-server

# RUN apt-get install -y --fix-missing xbase-clients

# Download latest version of McWeb repo
RUN git clone https://github.com/rasmunk/McWeb.git

# Run the McWeb setup script
RUN cd McWeb/scripts/ \
#    && ./bootstrap-docker.sh -d ${DJANGO} -m ${MPI}
