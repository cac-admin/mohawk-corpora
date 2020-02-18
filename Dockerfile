# Use an official Python runtime as a parent image
FROM python:3.7.4-slim

# Install required system packages
RUN apt-get update && \
    apt-get -y install gcc
RUN apt-get -y install ffmpeg

# Bower stuff, which we need to get rid of
RUN apt-get -y install git
RUN apt-get -y install npm
RUN npm install -g bower 

# Required for compilemessages in django
RUN apt-get -y install gettext


# Create necessary folders and files
RUN mkdir /webapp
RUN mkdir /webapp/logs
RUN touch /webapp/logs/celery.log
RUN touch /webapp/logs/django.log
RUN mkdir /webapp/run/


# Copy files over
COPY corpora /webapp/corpora/corpora
COPY requirements.txt /webapp/corpora/
COPY local.env /webapp/local.env
COPY entry.sh /webapp/corpora/

# Install any needed packages specified in requirements.txt
WORKDIR /webapp/corpora/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Temp hack to get things working
# We need to install the wahi-korero package
RUN pip install pydub webrtcvad

# Make port 80 available to the world outside this container
# EXPOSE 80

RUN bash