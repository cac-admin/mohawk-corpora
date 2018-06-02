from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording, Sentence
from transcription.models import Transcription
from corpus.views.views import RecordingFileView
from django.contrib.sites.shortcuts import get_current_site

from people.helpers import get_current_known_language_for_person

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
    api_url = "https://waha-tuhi.dragonfly.nz/transcribe"

    # the file_object could be in memory for small files and a temp file for
    # large files. we need to handle this. currently assuming small files
    # in memory
    # https://docs.djangoproject.com/en/2.0/ref/files/uploads/

    p = Popen(
        ['ffmpeg', '-i', '-', '-ar', '16000', '-ac', '1', '-f', 's16le', '-'],
        stdin=PIPE, stdout=PIPE)

    file_object.open()
    output, errors = p.communicate(file_object.read())
    file_object.close()

    headers = {
        'x-api-token': settings.TRANSCODE_API_TOKEN,
        'content-type': 'audio/x-wav'
    }

    logger.debug(u'Sending request to {0}'.format(api_url))

    try:
        response = requests.post(
            api_url,
            data=output,
            timeout=10,
            headers=headers)
        logger.debug(response.text)

        result = json.loads(response.text)

    except requests.exceptions.ConnectTimeout:

        result = {
            'success': False,
            'transcription': 'Could not get a transcription.'
        }

    recording.sentence_text = result['transcription'].strip()
    recording.save()
    if result['success']:

        # Get or create a source for the API
        source, created = Source.objects.get_or_create(
            source_name='Transcription API',
            author="{0}".format(result['api']),
            source_type='M',
            source_url=api_url)

        # Create a new sentence (because why not though this could blow things up in the future!)
        sentence, created = Sentence.objects.get_or_create(
            text=result['transcription'].strip())
        known_language = get_current_known_language_for_person(recording.person)

        if created:
            sentence.source = source
            sentence.language = known_language.language
            sentence.dialect = known_language.dialect
            sentence.save()

        # Create a new transcription
        transcription = Transcription.objects.create(
            recording=recording,
            text=result['transcription'].strip(),
            source=source)
        transcription.save()

    return recording.sentence_text


@shared_task
def transcribe_audio_task(recording_id):
    recording = Recording.objects.get(id=recording_id)
    response = transcribe_audio(recording, recording.audio_file)
    return response
