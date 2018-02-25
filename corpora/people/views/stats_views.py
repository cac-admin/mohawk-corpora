# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse

from django.urls import reverse, resolve
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
import json
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView, MultipleObjectMixin

from django.contrib.contenttypes.models import ContentType

from corpus.models import Recording, Sentence, QualityControl
from people.models import Person, KnownLanguage
from corpus.helpers import get_next_sentence
from people.helpers import get_or_create_person, get_person, get_current_language
from django.conf import settings

from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView

from boto.s3.connection import S3Connection

from django.db.models import Sum, Count, When, Value, Case, IntegerField, Q
from django.core.cache import cache

from corpus.aggregate import get_num_approved, get_net_votes

from django.contrib.auth.mixins import UserPassesTestMixin

from django.db import models

import logging
logger = logging.getLogger('corpora')


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

    return {
        'total': recording_queryset.count(),
        'num_approved': get_num_approved(recording_queryset),
        'up_votes': recording_votes[0],
        'down_votes': recording_votes[1],
        'duration_display': "{:02d}:{:02d}:{:02d} ".format(
            hours, minutes, seconds),
        'total_seconds': int(total_seconds),
        'dimension_string': _('seconds') if total_seconds < 60 else _('minutes')
    }


class JSONResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return context


class PersonRecordingStatsView(JSONResponseMixin, TemplateView):
    template_name = 'people/person_recording_stats_view_detail.html'

    def get_context_data(self, **kwargs):
        context = \
            super(PersonRecordingStatsView, self).get_context_data(**kwargs)

        person = get_person(self.request)
        language = get_current_language(self.request)

        recordings = Recording.objects.filter(
            sentence__language=language,
            person=person)

        # Assume for now user is in NZ timezone = UTC + 12 hours
        time_offset = 13
        now = timezone.now() + datetime.timedelta(hours=time_offset)

        # Find the day for NZ, then take us back to utc time.
        today_begining = \
            datetime.datetime.combine(now, datetime.time()) - \
            datetime.timedelta(hours=time_offset)

        # This logical is compared against utc time - the default timezone for our data
        # I presume django deals with this timezoen stuff anyway?
        todays_recordings = recordings.filter(created__gte=today_begining).order_by('created')

        stats = {
            'recordings': build_recordings_stat_dict(recordings),
            'recordings_today': build_recordings_stat_dict(todays_recordings)
        }

        stats['recordings_today']['start_time'] = today_begining
        stats['recordings_today']['end_time'] = timezone.now()
        if todays_recordings:
            stats['recordings_today']['earliest_time'] = todays_recordings[0].created
            stats['recordings_today']['latest_time'] = todays_recordings[todays_recordings.count()-1].created

        context['person'] = person
        context['stats'] = stats

        return context

    def render_to_response(self, context):
        if self.request.GET.get('format') == 'json':
            return self.render_to_json_response(context)
        else:
            return super(PersonRecordingStatsView, self).render_to_response(context)

    def get_data(self, context):
        return context['stats']


class PeopleRecordingStatsView(UserPassesTestMixin, ListView):
    model = Person
    template_name = 'people/peoplestats_list.html'
    paginate_by = 50
    context_object_name = 'people'

    def test_func(self):
        return True
        # return self.request.user.is_staff

    def get_queryset(self):
        language = get_current_language(self.request)
        return Person.objects.filter(recording__sentence__language=language)\
            .annotate(num_recordings=models.Count('recording'))\
            .order_by('-num_recordings')

    def get_context_data(self, **kwargs):
        context = \
            super(PeopleRecordingStatsView, self).get_context_data(**kwargs)

        language = get_current_language(self.request)

        people = context['people']

        people = people.annotate(num_recordings=models.Count('recording'))

        for person in context['people']:
            # recordings = Recording.objects\
            #     .filter(person=person, sentence__language=language)
            # score = 0
            # for recording in recordings:
            #     score = score + recording.calculate_score()
            # person.score = int(score)
            person.num_recordings = person.recording_set.count()
            if person.user is None:
                person.name = 'Anonymous Kumara'
            elif person.user.username == '':
                person.name = 'Anonymous Kumara'
            else:
                person.name = person.user.username

        return context
