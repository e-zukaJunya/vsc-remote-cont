# use python 3.8 official image
FROM python:3.8-slim

# update apt-get
RUN apt-get update -y && apt-get upgrade -y

# install some packages
RUN apt-get install zip vim sudo -y && pip3 install awscli pipenv
