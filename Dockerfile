FROM ubuntu:18.04

# Get required commands for script
RUN apt update \
    && apt install -y git

# Download latest version of McWeb repo
RUN git clone --single-branch --branch patch https://github.com/rasmunk/McWeb.git

# Run the McWeb setup script
RUN cd McWeb/scripts/ \
#    && ./bootstrap-mcweb-standalone.sh