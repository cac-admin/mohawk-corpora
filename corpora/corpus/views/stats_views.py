# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

from django.views.generic.list import ListView

from corpus.models import Recording
from people.helpers import get_current_language

import datetime
from django.utils import timezone

from django.db.models import Sum

from corpora.mixins import SiteInfoMixin

import logging
logger = logging.getLogger('corpora')


class RecordingStatsView(SiteInfoMixin, ListView):
    model = Recording
    template_name = 'corpus/recordings_stats_list.html'
    # paginate_by = 50
    context_object_name = 'recordings'
    x_title = _('Recording Growth Rate.')
    x_description = _('Graph of recording growth over the last month.')

    def get_context_data(self, **kwargs):
        context = super(RecordingStatsView, self).get_context_data(**kwargs)
        user = self.request.user

        language = get_current_language(self.request)

        recordings = context['recordings'].order_by('-created')

        start_date = recordings.last().created
        end_date = recordings.first().created

        start_day = \
            timezone.make_aware(
                datetime.datetime.combine(start_date, datetime.time()),
                timezone.get_default_timezone())

        end_day = \
            timezone.make_aware(
                datetime.datetime.combine(end_date, datetime.time()),
                timezone.get_default_timezone())

        day_counter = 1
        timezone_shift = datetime.timedelta(hours=13)
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
        # next_day = next_day 
        while next_day < timezone.now() - timezone_shift:

            if counter == 0:
                start_30days_back = timezone.now() - datetime.timedelta(days=30)
                # if start_30days_back > next_day:
                tomorrow = timezone.make_aware(
                        datetime.datetime.combine(start_30days_back, datetime.time()),
                        timezone.get_default_timezone())
            r = recordings.filter(
                created__gte=next_day+timezone_shift,
                created__lt=tomorrow+timezone_shift)\
                .aggregate(Sum('duration'))
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

            # try:
            #     next_day = timezone.make_aware(
            #         tomorrow,
            #         timezone.get_default_timezone())
            # except:
            next_day = tomorrow
            tomorrow = tomorrow + day_offset
            counter = counter + 1

        context['labels'] = [key for key in data['recordings']]
        context['values'] = [data['recordings'][i] for i in data['recordings']]

        context['data'] = data
        context['start_day'] = start_day
        context['end_day'] = end_day
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        return context
