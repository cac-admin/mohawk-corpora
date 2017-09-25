# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.forms import modelform_factory
from django.http import HttpResponse
from django.urls import reverse, resolve
from django.core.exceptions import ValidationError
import json
from django.views.generic.list import ListView

from corpus.models import Recording, Sentence
from people.models import Person
from corpus.helpers import get_next_sentence
from people.helpers import get_or_create_person
from django.conf import settings

from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView

from boto.s3.connection import S3Connection

import logging
logger = logging.getLogger('corpora')


class SentenceListView(ListView):
    model = Sentence

    def get(self, request, *args, **kwargs):
        self.request = request
        return super(SentenceListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SentenceListView, self).get_context_data(**kwargs)
        user = self.request.user
        user.can_approve = user.is_staff
        context['user'] = user
        context['uuid'] = self.request.get_signed_cookie('uuid', 'none')
        return context


def submit_recording(request):
    return render(request, 'corpus/submit_recording.html')

def failed_submit(request):
    return render(request, 'corpus/failed_submit.html')

def record(request):
    # Get the person object from the user

    # if not request.user.is_authenticated(): return redirect(reverse('account_login'))

    person = get_or_create_person(request)

    if request.method == 'GET':
        if request.GET.get('sentence',None):
            sentence = Sentence.objects.get(pk=request.GET.get('sentence'))
        else:
            sentence = get_next_sentence(request)
            if sentence == None:
                return redirect('people:profile')

    # Generate a form model from the Recording model
    RecordingFormAJAX = modelform_factory(Recording, fields='__all__')

    # If page receives POST request, save the submitted audio data as a recording model
    if request.method == 'POST' and request.is_ajax():

        # Create a form from the Recording Form model
        form = RecordingFormAJAX(request.POST, request.FILES)

        # If the form is valid, save the new model and send back an OK HTTP Response
        if form.is_valid():
            recording = form.save()
            recording.save()
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'message': "Thank you for submitting a recording! Here's another sentence for you to record."
                }), 
                content_type='application/json',
            )

        # If the form is not valid, sent a 400 HTTP Response
        else:
            # errors = form.errors          
            response = HttpResponse(
                json.dumps({
                        'err': "Sorry, your recording did not save."
                    }),
                content_type='application/json'
            )
            response.status_code = 400

            return response

    # Load up the page normally with request and object context

    context = {'request': request,
               'person': person,
               'sentence': sentence,
               'uuid': request.get_signed_cookie('uuid', 'none')}

    response = render(request, 'corpus/record.html', context)
    response.set_signed_cookie('uuid', person.uuid, max_age=60*60*24*365)

    return response


class RecordingFileView(RedirectView):
    permanent = False

    def get_redirect_url(self, **kwargs):
        s3 = S3Connection(settings.AWS_ACCESS_KEY_ID,
                          settings.AWS_SECRET_ACCESS_KEY,
                          is_secure=True)
        # Create a URL valid for 60 seconds.
        return s3.generate_url(60, 'GET',
                               bucket=settings.AWS_STORAGE_BUCKET_NAME,
                               key=kwargs['filepath'],
                               force_http=True)

    def get(self, request, *args, **kwargs):
        m = get_object_or_404(Recording, pk=kwargs['pk'])
        u = request.user

        if u.is_authenticated() and u.is_staff:
            try:
                logger.debug(m.audio_file.filename)
                logger.debug(m.audio_file.path)
                url = self.get_redirect_url(filepath=m.audio_file.path)
            except:
                url = m.audio_file.url

            if url:
                if self.permanent:
                    return http.HttpResponsePermanentRedirect(url)
                else:
                    return http.HttpResponseRedirect(url)
            else:
                logger.warning('Gone: %s', self.request.path,
                               extra={
                                'status_code': 410,
                                'request': self.request
                               })
                return http.HttpResponseGone()
        else:
            raise http.Http404
