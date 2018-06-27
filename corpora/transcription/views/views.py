from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext as _

from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.forms import modelform_factory
from django.http import HttpResponse
from django.urls import reverse, resolve
from django.core.exceptions import ValidationError
import json
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
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

from corpora.mixins import SiteInfoMixin

from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.mixins import UserPassesTestMixin

from transcription.models import AudioFileTranscription, TranscriptionSegment

import logging
logger = logging.getLogger('corpora')


# def submit_recording(request):
#     return render(request, 'corpus/submit_recording.html')


# def failed_submit(request):
#     return render(request, 'corpus/failed_submit.html')


# def record_redirect(request):
#     return redirect(reverse('corpus:record'))

class DashboardView(SiteInfoMixin, UserPassesTestMixin, TemplateView):
    x_description = _('Reo API Dashboard')
    x_title = _('Dashboard')
    template_name = "transcription/dashboard.html"

    def test_func(self):
        return self.request.user.is_authenticated


class TranscribeView(SiteInfoMixin, UserPassesTestMixin, TemplateView):
    x_description = _('Tryout our new transcription demo!')
    x_title = _('Transcribe Demo')
    template_name = "transcription/transcribe_demo.html"

    def test_func(self):
        return self.request.user.is_authenticated

        # key = self.request.GET.get('key', '')

        # if key == '720031ba-4db3-11e8-88f9-8c8590055544':
        #     return True

        # return self.request.user.is_staff


class AudioFileTranscriptionView(
        SiteInfoMixin, UserPassesTestMixin, DetailView):
    model = AudioFileTranscription
    context_object_name = 'aft'
    template_name = 'transcription/audio_file_transcription_detail.html'

    def test_func(self):
        return self.request.user.is_authenticated

        key = self.request.GET.get('key', '')

        if key == '720031ba-4db3-11e8-88f9-8c8590055544':
            return True

        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super(
            AudioFileTranscriptionView, self).get_context_data(**kwargs)

        segments = TranscriptionSegment.objects\
            .filter(parent=context['aft'])\
            .order_by('start')

        context['segments'] = segments

        return context


class AudioFileTranscriptionListView(
        SiteInfoMixin, UserPassesTestMixin, ListView):
    model = AudioFileTranscription
    context_object_name = 'transcriptions'
    template_name = 'transcription/audio_file_transcription_list.html'

    def test_func(self):
        return self.request.user.is_authenticated

        key = self.request.GET.get('key', '')

        if key == '720031ba-4db3-11e8-88f9-8c8590055544':
            return True

        return self.request.user.is_staff
