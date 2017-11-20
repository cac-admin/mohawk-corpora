from __future__ import absolute_import, unicode_literals
from celery import shared_task

from people.models import Person
from corpus.models import Recording

import logging
logger = logging.getLogger('corpora')


@shared_task
def clean_empty_person_models():
    people = Person.objects\
        .filter(full_name='')\
        .filter(user__isnull=True)\
        .filter(demographic__isnull=True)\
        .filter(known_languages__isnull=True)

    if len(people) == 0:
        logger.debug('No person models to clean')
    else:
        logger.debug('Found {0} to clean'.format(len(people)))

    for person in people:
        recordings = Recording.objects.filter(person=person)
        if len(recordings) == 0:
            logger.debug('Removing: {0}'.format(person))
            person.delete()
        else:
            logger.debug('Not removing {0} as recordings exist.'.format(person))
