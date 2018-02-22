from __future__ import absolute_import, unicode_literals
from celery import shared_task

from people.models import Person

import logging
logger = logging.getLogger('corpora')


@shared_task
def clean_empty_person_models():
    from corpus.models import Recording

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


@shared_task
def calculate_person_scores():
    from corpus.models import Recording, QualityControl

    people = Person.objects.all()

    # Notes, we calculte regardless of language!
    # That can be okay - e.g. finish one language move
    # onto another?
    for person in people:
        recordings = Recording.objects.filter(person=person)
        qcs = QualityControl.objects.filter(person=person)

        score = 0

        for r in recordings:
            score = score + float(r.calculate_score())

        for q in qcs:
            score = score + float(q.calculate_score())

        person.score = int(score)
        person.save()


@shared_task
def update_person_score(person_pk):
    from corpus.models import Recording, QualityControl

    try:
        person = Person.objects.get(pk=person_pk)
    except ObjectDoesNotExist:
        return "Person with pk {0} does not exist.".format(person_pk)

    # Notes, we calculte regardless of language!
    # That can be okay - e.g. finish one language move
    # onto another?

    recordings = Recording.objects.filter(person=person)
    qcs = QualityControl.objects.filter(person=person)

    score = 0

    for r in recordings:
        score = score + float(r.calculate_score())

    for q in qcs:
        score = score + float(q.calculate_score())

    person.score = score
    person.save()
