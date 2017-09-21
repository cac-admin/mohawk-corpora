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
from people.helpers import get_or_create_person_from_user

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
        return context


class RecordSentenceListView(ListView):
    model = Sentence

    def get(self, request, *args, **kwargs):
        self.request = request
        return super(RecordSentenceListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SentenceListView, self).get_context_data(**kwargs)
        user = self.request.user
        user.can_approve = user.is_staff
        context['user'] = user
        return context


def submit_recording(request):
    return render(request, 'corpus/submit_recording.html')

def failed_submit(request):
    return render(request, 'corpus/failed_submit.html')

def record(request):
    # Get the person object from the user

    # if not request.user.is_authenticated(): return redirect(reverse('account_login'))

    person = get_or_create_person_from_user(request.user)

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
        'sentence': sentence
        }

    return render(request, 'corpus/record.html', context)