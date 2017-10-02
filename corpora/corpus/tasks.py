from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.core.exceptions import ObjectDoesNotExist
from corpus.models import Recording

import wave
import contextlib

import logging
logger = logging.getLogger('corpora')


@shared_task
def encode_recording(recording):
    pass


@shared_task
def set_recording_length(recording_pk):
    try:
        recording = Recording.objects.get(pk=recording_pk)
    except ObjectDoesNotExist:
        logger.warning('Tried to get recording that doesn\'t exist')

    with contextlib.closing(wave.open(recording.audio_file, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        length = frames / float(rate)

    recording.duration = length
    recording.save()


@shared_task
def set_all_recording_durations():
    recordings = Recording.objects.filter(duration__lte=0)
    for recording in recordings:
        set_recording_length(recording.pk)
