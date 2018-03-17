# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import math
import decimal
from celery import shared_task
from django.utils.translation import ugettext as _

from django.conf import settings
from django.utils import translation, timezone
from django.core.exceptions import ObjectDoesNotExist

from people.models import Person, KnownLanguage, Group
from people.helpers import get_email, set_current_language_for_person, email_verified

from corpus.aggregate import build_recordings_stat_dict
from corpus.models import Recording

from celery.task.control import revoke, inspect

from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site

from django.db.models import Sum, Count, When, Value, Case, IntegerField
from django.db.models import Q, F
from django.db.models.functions import Length

from django.core.cache import cache

from django.utils.dateparse import parse_datetime
import pytz

import logging
logger = logging.getLogger('corpora')


def get_invalid_group_members(group, queryset=None):
    '''Get person objects that won't qualify to be in a group'''

    if queryset is None:
        queryset = Person.objects.all()

    # Complex query sets on related models causing problem
    # likely because it cant handle when emailaddress is null
    # for exmple there fore i will do old fashined way.

    queryset = queryset\
        .annotate(num_groups=Count('groups', distinct=True))\
        .filter(groups=group)\

    valid_pks = []
    for p in queryset:
        # Must have a valid email address
        # Must have a username of length > 0
        # Can only belong to one group
        verified_email = email_verified(p)
        if verified_email:
            if p.num_groups == 1:
                if p.username is not None:
                    if len(p.username) > 1:
                        valid_pks.append(p.pk)

    queryset = queryset.exclude(pk__in=valid_pks)

    return queryset


def get_valid_group_members(group, queryset=None):

    if queryset is None:
        queryset = Person.objects.all()

    invalid = get_invalid_group_members(group, queryset)
    invalid_pks = [p.pk for p in invalid]
    queryset = queryset\
        .annotate(num_groups=Count('groups', distinct=True))\
        .filter(groups=group)\
        .exclude(pk__in=invalid_pks)

    return queryset


def filter_recordings_for_competition(queryset):
    '''Takes a recording queryset and returns only recordings to be used during the
    competition. If the competition hasn't started or has ended, then this just
    returns the given queryset'''
    start = parse_datetime("2018-03-15 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-25 18:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    if timezone.now() < start:
        return queryset
    elif timezone.now() > end:
        return queryset
    else:

        queryset = queryset\
            .filter(created__lte=end)\
            .filter(created__gte=start)

    return queryset


def get_competition_group_score(group):
    start = parse_datetime("2018-03-15 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-25 18:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    # ERROR! This doesn't consder language!
    members = get_valid_group_members(group)
    if members is None:
        return 0

    SCORE_KEY = "COMP-GROUP-SCORE-{0}".format(group.pk)
    COUNT_KEY = "COMP-GROUP-COUNT-{0}".format(group.pk)
    score = cache.get(SCORE_KEY)
    count = cache.get(COUNT_KEY)
    if score is None:
        score = 0
        count = 0
        for person in members:
            p_score, p_count = get_competition_person_score(group, person)
            score = score + p_score
            count = count + p_count
        score = int(score)
        cache.set(SCORE_KEY, score, 60)
        cache.set(COUNT_KEY, count, 60)
    return score, count


def get_competition_person_score(group, person):
    start = parse_datetime("2018-03-15 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-25 18:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    # ERROR! This doesn't consder language!
    members = get_valid_group_members(group)
    if members is None:
        return 0

    # IMPORTANT CHANGE - LET THEM NO THEIR SCORES WILL SHOW HERE SO THAT
    # WHEN THEIR USER BECOMES VALID THEY'LL GET THEIR SCORES
    # if not members.filter(pk=person.pk).exists():
    #     return 0

    recordings = Recording.objects\
        .filter(person=person)\
        .filter(created__lte=end)\
        .filter(created__gte=start)

    SCORE_KEY = "COMP-PERSON-SCORE-{0}".format(person.pk)
    score = cache.get(SCORE_KEY)
    if score is None:
        score = 0
        for r in recordings:
            score = score + calculate_recording_score(r)
        cache.set(SCORE_KEY, score, 60)
    return score, recordings.count()


# TODO TEST THIS!
def calculate_recording_score(recording):
    """Score awarded for uploading this recording. """
    start = parse_datetime("2018-03-18 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-19 13:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    factor_1 = 1
    if recording.created > start and recording.created < end:
        factor_1 = 2

    approved = recording.quality_control \
        .filter(person__user__is_staff=True) \
        .filter(approved=True)

    if approved.count() >= 1:
        return 1

    net_votes = recording.quality_control \
        .filter(person__user__is_staff=True) \
        .aggregate(value=Sum(F('good') - F('bad')))

    net_votes = decimal.Decimal(net_votes['value'] or 0)

    if net_votes != 0:
        net_votes = net_votes/abs(net_votes)

    damper = 4
    score = max(0, 1 - math.exp(-(net_votes + 1) / damper))

    if net_votes == 0:
        return score * factor_1
    else:
        return score
