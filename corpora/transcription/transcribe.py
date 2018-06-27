from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording, Sentence, Source
from transcription.models import \
    Transcription, TranscriptionSegment, AudioFileTranscription
from corpus.views.views import RecordingFileView
from django.contrib.sites.shortcuts import get_current_site

from corpora.utils.tmp_files import prepare_temporary_environment
from people.helpers import get_current_known_language_for_person

from transcription.utils import create_and_return_transcription_segments

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


def parse_sphinx_transcription(lines):
    transcription = []
    new_list = []
    append = False
    for item in lines:
        parts = item.split(" ")
        obj = parts.pop(0)

        for part in parts:
            try:
                float(part)
                append = True
            except:
                append = False
                break
        if append:
            new_list.append(item)
            if obj not in ["<s>", "</s>", "<sil>"] and len(parts) == 3:
                transcription.append(obj)

    text = " ".join(transcription)
    return text


def transcribe_audio_sphinx(audio, continuous=False, file_path=None):
    # api_url = "https://waha-tuhi.dragonfly.nz/transcribe"
    # DeepSpeech: http://waha-tuhi-api-17.dragonfly.nz
    API_URL = "http://waha-tuhi-api-17.dragonfly.nz/transcribe"
    if continuous:
        pass  # not available with deepspeech
        # API_URL = "http://waha-tuhi-api-15.dragonfly.nz/transcribe_continuous"

    # the file_object could be in memory for small files and a temp file for
    # large files. we need to handle this. currently assuming small files
    # in memory
    # https://docs.djangoproject.com/en/2.0/ref/files/uploads/

    if file_path:
        f = open(file_path, 'rb')
        audio = f.read()
        f.close()

    headers = {
        'x-api-token': settings.TRANSCODE_API_TOKEN,
        'content-type': 'audio/x-wav',
        'Accept': 'application/json',
    }

    logger.debug(u'Sending request to {0}'.format(API_URL))

    try:
        response = requests.post(
            API_URL,
            data=audio,
            timeout=10,
            headers=headers)
        logger.debug(u'{0}'.format(response.text))

        result = json.loads(response.text)

    except requests.exceptions.ConnectTimeout:

        result = {
            'success': False,
            'transcription': 'Could not get a transcription.'
        }

    result['API_URL'] = API_URL

    return result


def transcribe_audio(recording, file_object):

    file_object.open()
    p = Popen(
        ['ffmpeg', '-i', '-', '-ar', '16000', '-ac', '1',  '-'],  # '-f', 's16le',
        stdin=PIPE, stdout=PIPE)

    output, errors = p.communicate(file_object.read())
    file_object.close()

    # result2 = transcribe_audio_sphinx(output, continuous=True)
    result = transcribe_audio_sphinx(output)

    recording.sentence_text = result['transcription'].strip()
    recording.save()
    if result['success']:

        # Get or create a source for the API
        source, created = Source.objects.get_or_create(
            source_name='Transcription API',
            author="{0}".format(result['model_version']),
            source_type='M',
            source_url=result['API_URL'])

        # Create a new sentence (because why not though this could blow things up in the future!)
        # We should only do this if they're using the live demo on the website
        # This makes sense if a person is reading freely to the machine
        # But doesn't make sense if someone is uploading a recording from
        # somewhere else.
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


@shared_task
def transcribe_segment_async(ts_id):
    ts = TranscriptionSegment.objects.get(pk=ts_id)
    try:
        result = transcribe_segment(ts)
    except Exception as e:
        return "{0}".format(e)

    return result


def transcribe_segment(ts):
    try:
        file_path, tmp_stor_dir, tmp_file, absolute_directory = \
            prepare_temporary_environment(ts.parent)
    except Exception as e:
        return "Error creating temporary environment. {0}".format(e)

    tmp_seg_file = tmp_stor_dir + '/ts_{0}.wav'.format(ts.pk)

    command = \
        ['ffmpeg', '-i', tmp_file,
         '-ss', '{0:.2f}'.format(ts.start/100.0),
         '-to', '{0:.2f}'.format(ts.end/100.0),
         '-ar', '16000', '-ac', '1',  # '-f', 's16le',
         tmp_seg_file]

    logger.debug("COMMAND: {0}".format(' '.join(command)))

    p = Popen(command, stdin=PIPE, stdout=PIPE)

    output, errors = p.communicate()
    # result = transcribe_audio_sphinx(output)
    result = transcribe_audio_sphinx(
        None, continuous=True, file_path=tmp_seg_file)

    if result['success']:

        ts.text = parse_sphinx_transcription(result['transcription'])
        ts.transcriber_log = result
        # Get or create a source for the API
        source, created = Source.objects.get_or_create(
            source_name='Transcription API',
            author="{0}".format(result['model_version']),
            source_type='M',
            source_url=result['API_URL'])

        ts.source = source

        ts.save()
    else:
        ts.transcriber_log = result
        ts.save()


@shared_task
def transcribe_aft_async(pk):
    aft = AudioFileTranscription.objects.get(pk=pk)
    segments = create_and_return_transcription_segments(aft)
    if len(segments) == 0:
        return "ERROR: NO SEGMENTS CREATED"

    results = []
    for segment in segments:
        transcribe_segment(segment)

    return "WINNING!"
