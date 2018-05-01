from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording
from corpus.views.views import RecordingFileView
from django.contrib.sites.shortcuts import get_current_site

from django.core.files import File
import wave
import contextlib
import os
import stat
import commands
import ast
import sys
import requests
import urllib2
import json
from subprocess import Popen, PIPE
import time

from django.core.cache import cache

import logging
logger = logging.getLogger('corpora')


def transcribe_audio(recording, file_object):
    api_url = "http://waha-tuhi.dragonfly.nz/transcribe"
    command = "curl --request POST --data-binary \"@5{0}\" {1}"
    file_name = recording.audio_file.name.split('/')[-1]

    # the file_object could be in memory for small files and a temp file for
    # large files. we need to handle this. currently assuming small files
    # in memory
    # https://docs.djangoproject.com/en/2.0/ref/files/uploads/

    # p = Popen(
    #     ['ffmpeg', '-i', '-', '-ar', '16000', '-ac', '1', '-f', 's16le', '-'],
    #     stdin=PIPE, stdout=PIPE)

    # # p.communicate(input=file_object)
    # for chunk in file_object.chunks():
    #     p.stdin.write(chunk)
    # p.stdin.close()
    # p.stdin.write(file_object)

    response = requests.post(
        api_url,
        data=file_object,
        timeout=10)

    # response = urllib2.urlopen(urllib2.Request(
    #     api_url, file_object, {'Content-Type': 'audio/wav'}))

    logger.debug(response.text)

    result = json.loads(response.text)

    if result['success']:
        recording.sentence_text = result['transcription'].strip()
        recording.save()

    return response.text


@shared_task
def transcribe_audio_task(recording_id):
    recording = Recording.objects.get(id=recording_id)

    recording.audio_file_wav.open()
    file_object = recording.audio_file_wav.read()
    recording.audio_file_wav.close()

    response = transcribe_audio(recording, file_object)

    return response
