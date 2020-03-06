FROM ubuntu:18.04

RUN apt update

RUN apt install -y git

RUN git clone --single-branch --branch patch https://github.com/rasmunk/McWeb.git
