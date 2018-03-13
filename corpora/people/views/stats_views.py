# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden

from django.urls import reverse, resolve
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
import json
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView, MultipleObjectMixin
from django.views.generic.detail import DetailView
from django.middleware.csrf import CsrfViewMiddleware

from django.contrib.contenttypes.models import ContentType

from corpus.models import Recording, Sentence, QualityControl
from people.models import Person, KnownLanguage, Group
from people.tasks import send_person_emails
from people.forms import SendEmailForm
from corpus.helpers import get_next_sentence
from people.helpers import get_or_create_person, get_person, get_current_language
from django.conf import settings

from allauth.account.models import EmailAddress

from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView

from boto.s3.connection import S3Connection

from django.db.models import Sum, Count, When, Value, Case, IntegerField, Q
from django.core.cache import cache

from corpus.aggregate import build_recordings_stat_dict

from django.contrib.auth.mixins import UserPassesTestMixin

from django.db import models

from corpora.mixins import SiteInfoMixin

from people.competition import \
    get_competition_group_score,\
    get_valid_group_members,\
    get_invalid_group_members


import logging
logger = logging.getLogger('corpora')


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
    template_name = 'people/stats/person_recording_stats_view_detail.html'

    def get_context_data(self, **kwargs):
        context = \
            super(PersonRecordingStatsView, self).get_context_data(**kwargs)

        person = get_person(self.request)
        language = get_current_language(self.request)

        recordings = Recording.objects.filter(
            sentence__language=language,
            person=person)

        # Assume for now user is in NZ timezone = UTC + 12 hours
        time_offset = 0
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


class PeopleRecordingStatsView(SiteInfoMixin, UserPassesTestMixin, ListView):
    model = Person
    template_name = 'people/stats/leaderboard.html'
    paginate_by = 50
    context_object_name = 'people'
    x_title = _('Leaderboard')
    x_description = \
        _("Leaderboard for people who've contributed to our corpus.")

    def test_func(self):
        return True
        # return self.request.user.is_staff

    def get_queryset(self):
        language = get_current_language(self.request)
        return Person.objects\
            .filter(recording__sentence__language=language)\
            .exclude(leaderboard=False)\
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


class GroupsStatsView(SiteInfoMixin, UserPassesTestMixin, ListView):
    model = Group
    template_name = 'people/stats/groups_leaderboard.html'
    paginate_by = 50
    context_object_name = 'groups'
    x_title = _('Group Leaderboard')
    x_description = _("Group leaderboard of all the groups contributing corpus\
to our project.")

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        # language = get_current_language(self.request)
        return Group.objects.all().order_by('name').order_by('-score')\
            .annotate(size=Count('person'))

    def get_context_data(self, **kwargs):
        context = \
            super(GroupsStatsView, self).get_context_data(**kwargs)

        language = get_current_language(self.request)

        groups = context['groups']
        for group in groups:
            people = Person.objects\
                .annotate(num_groups=Count('groups'))\
                .filter(groups__pk=group.pk)\
                .filter(num_groups=1)
            d = people.aggregate(num_recordings=Count('recording'))
            group.num_recordings = d['num_recordings']

        return context


class GroupStatsView(SiteInfoMixin, UserPassesTestMixin, DetailView):
    model = Group
    template_name = 'people/stats/group_leaderboard.html'
    context_object_name = 'group'
    x_title = _('Individual Group Leaderboard')
    x_description = _("Leaderboard for people of a particular group.")

    def test_func(self):
        person = get_person(self.request)
        path = self.request.get_full_path()
        pk = int(path.split('/')[-1])

        if self.request.user.is_staff:
            return True
        elif pk in person.groups.filter(pk__in=[pk]).exists():
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = \
            super(GroupStatsView, self).get_context_data(**kwargs)

        group = context['group']

        x_title = _('Group Leaderboard: {0}').format(group)
        x_description = _("Leaderboard for members of {0}.").format(
            group)

        language = get_current_language(self.request)

        people = Person.objects\
            .filter(recording__sentence__language=language)

        valid_members = people
        valid_members = get_valid_group_members(group, valid_members)

        invalid_members = people
        invalid_members = get_invalid_group_members(group, invalid_members)

        score = get_competition_group_score(group)

        if valid_members:
            valid_members = valid_members\
                .annotate(num_recordings=Count('recording'))

        if invalid_members:
            invalid_members = invalid_members\
                .annotate(num_groups=Count('groups', distinct=True))
            for p in invalid_members:
                try:
                    p.verified = p.user.emailaddress.verified
                except:
                    p.verified = False


        # for person in invalid_members:
            # person.num_groups = person.groups.all().count()

        context['valid_members'] = valid_members
        context['invalid_members'] = invalid_members

        return context


class PeopleEmailsView(UserPassesTestMixin, ListView):
    model = Person
    template_name = 'people/people_email_list.html'
    context_object_name = 'people'
    raise_exception = True
    paginate_by = 495

    def test_func(self):
        return self.request.user.is_superuser \
            and self.request.user.is_authenticated

    def get_queryset(self):
        return Person.objects\
            .filter(Q(profile_email__isnull=False) | Q(user__isnull=False))\
            .exclude(receive_weekly_updates=False)\
            .order_by('full_name')

    def get_context_data(self, **kwargs):
        context = \
            super(PeopleEmailsView, self).get_context_data(**kwargs)

        form = SendEmailForm()
        context['form'] = form

        people = context['people']

        for person in context['people']:
            if person.user is not None:
                try:
                    email = EmailAddress.objects.get(user=person.user)
                    email = email.email
                except ObjectDoesNotExist:
                    email = person.user.email
                except MultipleObjectsReturned:
                    try:
                        email = EmailAddress.objects.get(
                            user=person.user, verified=True)
                        email = email.email
                    except ObjectDoesNotExist:
                        email = EmailAddress.objects.filter(user=person.user).first()
                        email = email.email
            else:
                email = person.profile_email

            person.email = email

        return context

    def post(self, request, *args, **kwargs):
        reason = CsrfViewMiddleware().process_view(request, None, (), {})
        if reason:
            raise PermissionException()

        if not self.request.user.is_superuser and \
                self.request.user.is_authenticated:
            return HttpResponseForbidden()

        # Everything is okay - so let's send emails?

        form = SendEmailForm(request.POST)
        if form.is_valid():
            freq = []
            if form.cleaned_data['weekly']:
                freq.append(_('weekly'))
            if form.cleaned_data['daily']:
                freq.append(_('daily'))

            for f in freq:
                send_person_emails.apply_async(
                    countdown=2,
                    task_id='send_{0}_emails-{1}'.format(
                        f, timezone.now().strftime("%y%m%d-%H")),
                    args=[f])

        return super(PeopleEmailsView, self).get(request, *args, **kwargs)
