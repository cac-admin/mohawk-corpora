from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings

from django.core.exceptions import ObjectDoesNotExist
from people.models import Person
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

import logging
logger = logging.getLogger('corpora')


@shared_task
def clean_empty_person_models():
    people = Person.objects\
        .filter(full_name__isnull=True)\
        .filter(user__isnull=True)\
        .filter(demographic__isnul=True)\
        .filter(known_language__isnull=True)

    for person in people:
        recordings = Recording.objects.filter(person=person)
        if len(recordings) == 0:
            logger.debug('Removing: {0}'.format(person))
            person.delete()
