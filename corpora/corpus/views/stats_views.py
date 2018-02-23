# -*- coding: utf-8 -*-
# from django.shortcuts import render, redirect
# from django.template.context import RequestContext
# from django.forms import modelform_factory
# from django.http import HttpResponse
# from django.urls import reverse, resolve
# from django.core.exceptions import ValidationError
# import json
from django.views.generic.list import ListView
# from django.views.generic.base import TemplateView
# from django.contrib.contenttypes.models import ContentType

from corpus.models import Recording
# from people.models import Person, KnownLanguage
# from corpus.helpers import get_next_sentence
from people.helpers import get_current_language

import datetime
from django.utils import timezone
# from django.conf import settings

# from django import http
# from django.shortcuts import get_object_or_404
# from django.views.generic import RedirectView

# from boto.s3.connection import S3Connection

from django.db.models import Sum  # , Count, When, Value, Case, IntegerField, Q
# from django.core.cache import cache

# from corpus.aggregate import get_num_approved, get_net_votes

import logging
logger = logging.getLogger('corpora')


class RecordingStatsView(ListView):
    model = Recording
    template_name = 'corpus/recordings_stats_list.html'
    # paginate_by = 50
    context_object_name = 'recordings'

    def get_context_data(self, **kwargs):
        context = super(RecordingStatsView, self).get_context_data(**kwargs)
        user = self.request.user

        language = get_current_language(self.request)

        recordings = context['recordings'].order_by('-created')

        start_date = recordings.last().created
        end_date = recordings.first().created

        start_day = \
            datetime.datetime.combine(start_date, datetime.time())
        end_day = \
            datetime.datetime.combine(end_date, datetime.time())

        day_counter = 1
        day_offset = datetime.timedelta(days=day_counter)
        next_day = start_day
        data = {'recordings': {}, 'growth_rate': {}}

        data = {
            'recordings': {
                'labels': [],
                'values': [],
            },
            'growth_rate': {
                'labels': [],
                'values': [],
            },
        }

        total_recordings = 0
        counter = 0
        tomorrow = next_day + day_offset
        while next_day < end_day + day_offset:

            if counter == 0:
                start_30days_back = datetime.datetime.today() - datetime.timedelta(days=30)
                if start_30days_back > next_day:
                    tomorrow = datetime.datetime.combine(start_30days_back, datetime.time())
            r = recordings.filter(
                created__gte=next_day,
                created__lt=tomorrow).aggregate(Sum('duration'))
            if r['duration__sum'] is None:
                r['duration__sum'] = 0

            total_recordings = int(r['duration__sum']/60) + total_recordings

            data['recordings']['labels'].append(
                (tomorrow).strftime('%d-%m-%y'))
            data['recordings']['values'].append(total_recordings)

            try:
                data['growth_rate']['labels'].append(
                    (tomorrow).strftime('%d-%m-%y'))
                data['growth_rate']['values'].append(
                    total_recordings - data['recordings']['values'][counter-1])
            except IndexError:
                data['growth_rate']['values'].append(total_recordings)

            next_day = tomorrow
            tomorrow = tomorrow + day_offset
            counter = counter + 1

        context['labels'] = [key for key in data['recordings']]
        context['values'] = [data['recordings'][i] for i in data['recordings']]

        context['data'] = data
        context['start_day'] = start_day
        context['end_day'] = end_day
        return context
