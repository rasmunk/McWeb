FROM ubuntu:18.04

# -- Configuration variables --
# tzdata
ARG region=Europe
ARG city=Copenhagen
# Django 
ARG DJANGO=Passw0rd123
# MPI cores
ARG MPI=1

# Get required commands for script
RUN apt update
RUN apt install -y git
RUN apt install -y net-tools
RUN apt install -y iproute2
RUN apt install -y sudo
RUN apt install -y openssh-server
RUN apt install -y xbase-clients
RUN apt install -y zip
RUN apt install -y unzip
RUN apt install -y cron
RUN apt install -y curl
RUN apt install -y lsof

RUN DEBIAN_FRONTEND=noninteractive apt install -y keyboard-configuration

# Install and configure tzdata for bootstrap script
RUN ln -fs /usr/share/zoneinfo/${region}/${city} /etc/localtime \
    && apt-get install -y tzdata

# Download latest version of McWeb repo
RUN git clone https://github.com/rasmunk/McWeb.git

# Run the McWeb setup script
RUN cd McWeb/scripts/ \
#    && ./bootstrap-docker.sh -d ${DJANGO} -m ${MPI}
