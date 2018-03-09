# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils.translation import ugettext as _

from django.conf import settings
from django.utils import translation, timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum

from people.models import Person, KnownLanguage, Group
from people.helpers import get_email, set_current_language_for_person

from corpus.aggregate import build_recordings_stat_dict
from corpus.models import Recording

from celery.task.control import revoke, inspect

from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site

import datetime

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
def clean_empty_group_models():
    from corpus.models import Recording

    groups = Group.objects.all()

    for group in groups:
        if group.person_set.count() == 0:
            logger.debug('Removing: {0}'.format(group))
            group.delete()


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

        # for q in qcs:
        #     score = score + float(q.calculate_score())

        person.score = int(score)
        person.save()

    return "Updated {0} scores".format(people.count())


@shared_task
def calculate_group_scores():
    from corpus.models import Recording, QualityControl

    groups = Group.objects.all()

    for group in groups:

        update_group_score.apply_async(
            args=[group.pk],
            task_id="update-group-score-{0}-{1}".format(
                group.pk, timezone.now().strftime("%M")),
            countdown=42)

    return "Updated {0} scores".format(groups.count())


@shared_task
def update_group_score(g_pk):
    from corpus.models import Recording, QualityControl

    try:
        group = Group.objects.get(pk=g_pk)
    except ObjectDoesNotExist:
        return "Group with pk {0} does not exsit.".format(g_pk)

    people = Person.objects\
        .annotate(num_groups=Count('groups'))\
        .filter(groups__pk=g_pk)\
        .filter(num_groups=1)

    d = people.aggregate(total_score=Sum('score'))

    if d['total_score']:
        group.score = int(d['total_score'])
        group.save()
        return "New score for {0}: {1}.".format(g_pk, group.score)
    else:
        return "No score for {0}.".format(g_pk)


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

    # for q in qcs:
    #     score = score + float(q.calculate_score())

    person.score = score
    person.save()

    groups = person.groups.all()
    for g in groups:
        update_group_score.apply_async(
            args=[g.pk],
            task_id="update-group-score-{0}-{1}".format(
                g.pk, timezone.now().strftime("%M")),
            countdown=42)

    return "New score for {0}: {1}".format(person_pk, score)


@shared_task
def send_person_emails_staff(frequency='weekly'):
    '''Send an email to all staff. This is being implemented for testing
    purposes but also so we can send different emails to staff with different
    priviledges'''
    people = Person.objects\
        .filter(user__is_staff=True)\
        .filter(**{'receive_{0}_updates'.format(frequency): True})

    count = 1
    for person in people:
        if settings.DEBUG:
            p_display = person.profile_email
        else:
            p_display = person.pk
        result = send_status_email.apply_async(
            args=[person.pk, frequency],
            countdown=count,
            task_id='send_{1}_email-staff-{0}-{2}'.format(
                p_display, frequency, timezone.now().strftime("%y%m%d-%H"))
            )
        count = count+1
        logger.debug("Sending email to {0}".format(person))
    return "Sent emails to {0} staff.".format(count)


@shared_task
def send_person_emails(frequency='weekly'):
    '''Send a email to all people.'''

    counter = 0
    # Check if site is development
    if settings.DEBUG:
        send_person_emails_staff(frequency)
        return "This is a dev environment!"
    else:
        counter = 0

        people = Person.objects.filter(
            **{'receive_{0}_updates'.format(frequency): True})
        for person in people:
            try:
                logger.debug("Sending email to {0}".format(person))
                result = send_status_email.apply_async(
                    args=[person.pk, frequency],
                    countdown=2,
                    task_id='send_{1}_email-{0}-{2}'.format(
                        person.pk, frequency, timezone.now().strftime("%y%m%d-%H"))
                    )
                logger.debug(result)
                counter = counter + 1
            except:
                logger.debug("Email did not send for {0}".format(person))
    return "Sent {0} {1} emails.".format(counter, frequency)


@shared_task
def send_status_email(person_pk, frequency='weekly'):
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

    if 'daily' in frequency:
        time_delta = datetime.timedelta(days=1)
        period_of_time = _('today')
        previous_period_of_time = _('yesterday')
    else:
        time_delta = datetime.timedelta(days=7)
        period_of_time = _('this week')
        previous_period_of_time = _('last week')

    period = recordings.filter(created__gt=timezone.now()-time_delta)
    this_period_stats = build_recordings_stat_dict(period)

    period = recordings\
        .filter(created__lte=timezone.now()-time_delta)\
        .filter(created__gt=timezone.now()-2*time_delta)
    last_period_stats = build_recordings_stat_dict(period)

    email = get_email(person)

    if email:

        url_append = 'https://' + Site.objects.get_current().domain

        subject = "Your {0} update!".format(frequency)

        e = EMail(to=email, subject=subject)
        context = {
            'subject': subject,
            'person': person,
            'stats': stats,
            'this_period_stats': this_period_stats,
            'last_period_stats': last_period_stats,
            'total_duration': "{0:.1f}".format(hours),
            'url_append': url_append,
            'site': Site.objects.get_current(),
            'period_of_time': period_of_time,
            'previous_period_of_time': previous_period_of_time,
            'frequency': frequency}

        e.text('people/email/freq_stats_update.txt', context)
        e.html('people/email/freq_stats_update.html', context)

        if settings.DEBUG:
            p_display = email
        else:
            p_display = person_pk
        p_display = email
        result = e.send(
            from_addr='Kōrero Māori <koreromaori@tehiku.nz>',
            fail_silently='False')
        if result == 1:
            return "Sent email to {0}".format(p_display)
        else:
            return \
                "Error sending email to {0} - {1}.".format(p_display, result)

    else:
        return "No email associated with person."
