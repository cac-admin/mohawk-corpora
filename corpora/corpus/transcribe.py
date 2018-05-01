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

from django.core.cache import cache

import logging
logger = logging.getLogger('corpora')


def transcribe_audio(recording, file_object):
    api_url = "http://waha-tuhi.dragonfly.nz/transcribe"
    command = "curl --request POST --data-binary \"@5{0}\" {1}"
    file_name = recording.audio_file.name.split('/')[-1]

    logger.debug(recording)
    logger.debug(file_object)

    r = requests.post(
        api_url,
        files=[
            ('audio', (file_name, file_object, 'audio/x-wav'))
            ],
        timeout=10)

    logger.debug(r)

    return r
