# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.utils.translation import ugettext as _
from corpus.models import Recording, Sentence, QualityControl
from django.db.models import Sum, Count, When, Value, Case, IntegerField


def get_num_approved(query):
    d = query\
        .aggregate(sum_approved=Sum(
            Case(
                When(
                    quality_control__isnull=True,
                    then=Value(0)),
                When(
                    quality_control__approved=True,
                    then=Value(1)),
                When(
                    quality_control__approved=False,
                    then=Value(0)),
                default=Value(0),
                output_field=IntegerField())))
    return d['sum_approved']


def get_net_votes(query):
    d1 = query\
        .aggregate(total_up_votes=Sum('quality_control__good'))
    d2 = query\
        .aggregate(total_down_votes=Sum('quality_control__bad'))

    return (d1['total_up_votes'], d2['total_down_votes'])


def build_recordings_stat_dict(recording_queryset):
    duration = recording_queryset.aggregate(Sum('duration'))
    approved_recordings = \
        recording_queryset.filter(quality_control__approved=True)
    recording_votes = get_net_votes(recording_queryset)

    if duration['duration__sum'] is None:
        total_seconds = 0
    else:
        total_seconds = float(duration['duration__sum'])
    hours = int(total_seconds/(60.0*60))
    minutes = int((total_seconds - (60*60.0)*hours)/60.0)
    seconds = int(total_seconds - (60*60.0)*hours - 60.0*minutes)

    stats = {
        'total': recording_queryset.count(),
        'num_approved': get_num_approved(recording_queryset),
        'up_votes': recording_votes[0],
        'down_votes': recording_votes[1],
        'duration_display': "{:02d}:{:02d}:{:02d} ".format(
            hours, minutes, seconds),
        'total_seconds': int(total_seconds),
        'total_minutes': int(total_seconds/60.0),
        'dimension_string': _('seconds') if total_seconds < 60 else _('minutes')
    }

    if stats['up_votes'] is None:
        stats['up_votes'] = 0

    if stats['down_votes'] is None:
        stats['down_votes'] = 0

    if stats['num_approved'] is None:
        stats['num_approved'] = 0

    return stats
