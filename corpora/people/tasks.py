# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.conf import settings
from django.utils import translation
from django.core.exceptions import ObjectDoesNotExist

from people.models import Person, KnownLanguage
from people.helpers import get_email, set_current_language_for_person

from corpus.aggregate import build_recordings_stat_dict
from corpus.models import Recording

from celery.task.control import revoke, inspect

from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site


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
            logger.debug(
                'Not removing {0} as recordings exist.'.format(person))


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


@shared_task
def send_person_weekly_emails_staff():
    '''Send a weekly email to all staff. This is being implemented for testing
    purposes but also so we can send different emails to staff with different
    priviledges'''
    people = Person.objects.filter(user__is_staff=True)
    for person in people:
        print "Sending email to {0}".format(person)
        result = send_weekly_status_email(person.pk)
        print result


@shared_task
def send_person_weekly_emails():
    '''Send a weekly email to all staff. This is being implemented for testing
    purposes but also so we can send different emails to staff with different
    priviledges'''

    # Check if site is development
    if settings.DEBUG:
        print "This is a dev envrionment!"
    else:
        people = Person.objects.filter(receive_weekly_updates=True)
        for person in people:
            print "Sending email to {0}".format(person)
            result = send_weekly_status_email(person.pk)
            print result


@shared_task
def send_weekly_status_email(person_pk):
    from corpora.email_utils import EMail

    try:
        person = Person.objects.get(pk=person_pk)
    except ObjectDoesNotExist:
        return "No person with id {0} found.".format(person_pk)

    # Set the language - this is used when rendering the templates.
    language = translation.get_language()
    try:
        active_language = \
            KnownLanguage.objects.get(person=person, active=True)
        language = active_language.language
    except ObjectDoesNotExist:
        pass
    translation.activate(language)

    recordings = Recording.objects.all()
    stats = build_recordings_stat_dict(recordings)
    total_seconds = stats['total_seconds']
    hours = total_seconds/60.0/60.0
    recordings = recordings.filter(person=person)

    stats = build_recordings_stat_dict(recordings)

    email = get_email(person)

    if email:

        url_append = 'https://' + Site.objects.get_current().domain

        subject = "Your weekly update!"

        e = EMail(to=email, subject=subject)
        context = {
            'subject': subject,
            'person': person,
            'stats': stats,
            'total_duration': "{0:.1f}".format(hours),
            'url_append': url_append,
            'site': Site.objects.get_current()}

        e.text('people/email/weekly_stats_update.txt', context)
        e.html('people/email/weekly_stats_update.html', context)

        return e.send(
            from_addr='Kōrero Māori <koreromaori@tehiku.nz>',
            fail_silently='False')

    else:
        return "No email associated with person."
