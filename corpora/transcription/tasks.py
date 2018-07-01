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
import uuid
from subprocess import Popen, PIPE
import time


from django.core.cache import cache

import logging
logger = logging.getLogger('corpora')


@shared_task
def launch_transcription_api():
    num_jobs = cache.get('TRANSCRIPTION_JOBS', 0)

    logger.debug('NUM_TRANSCRIPTION_JOBS: {0: <4f}'.format(num_jobs))
