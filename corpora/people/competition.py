# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils.translation import ugettext as _

from django.conf import settings
from django.utils import translation, timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum

from people.models import Person, KnownLanguage, Group
from people.helpers import get_email, set_current_language_for_person, email_verified

from corpus.aggregate import build_recordings_stat_dict
from corpus.models import Recording

from celery.task.control import revoke, inspect

from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site

from django.db.models import Sum, Count, When, Value, Case, IntegerField
from django.db.models import Q
from django.db.models.functions import Length


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
        if verified_email and len(p.username)>1 and p.num_groups == 1:
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


def get_competition_group_score(group):
    start = parse_datetime("2018-03-15 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-25 18:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    # ERROR! This doesn't consder language!
    members = get_valid_group_members(group)
    if members is None:
        return 0
    score = 0
    for person in members:
        recordings = Recording.objects\
            .filter(person=person)\
            .filter(created__lte=end)\
            .filter(created__gte=start)
        for r in recordings:
            score = score + r.calculate_score()

    return score


def get_competition_person_score(group, person):
    start = parse_datetime("2018-03-15 13:00:00")
    start = pytz.timezone("Pacific/Auckland").localize(start, is_dst=None)
    end = parse_datetime("2018-03-25 18:00:00")
    end = pytz.timezone("Pacific/Auckland").localize(end, is_dst=None)

    # ERROR! This doesn't consder language!
    members = get_valid_group_members(group)
    if members is None:
        return 0

    if not members.filter(pk=person.pk).exists():
        return 0

    score = 0
    recordings = Recording.objects\
        .filter(person=person)\
        .filter(created__lte=end)\
        .filter(created__gte=start)
    for r in recordings:
        score = score + r.calculate_score()

    return score
