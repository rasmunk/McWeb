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
RUN apt update \
    && apt install -y git \
    && DEBIAN_FRONTEND=noninteractive apt install -y keyboard-configuration

# Install and configure tzdata for bootstrap script
RUN ln -fs /usr/share/zoneinfo/${region}/${city} /etc/localtime \
    && apt-get install -y tzdata

# Download latest version of McWeb repo
RUN git clone https://github.com/rasmunk/McWeb.git

# Run the McWeb setup script
RUN cd McWeb/scripts/ \
#    && ./bootstrap-docker.sh -d ${DJANGO} -m ${MPI}

