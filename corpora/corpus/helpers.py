# -*- coding: utf-8 -*-
from django.db.models import Sum, Case, When, Value, IntegerField
from corpus.models import Sentence
from people.helpers import get_current_language, get_or_create_person
import random
import logging
logger = logging.getLogger('corpora')


def get_sentences(request,
                  recordings=None,
                  person=None,
                  current_language=None):
    ''' Returns sentences without recordings '''

    if person is None:
        person = get_or_create_person(request)

    if current_language is None:
        current_language = get_current_language(request)

    sentences = Sentence.objects.filter(language=current_language)\
        .annotate(sum_approved=Sum(
            Case(
                When(
                    quality_control__approved=True,
                    then=Value(1)),
                When(
                    quality_control__approved=False,
                    then=Value(0)),
                default=Value(0),
                output_field=IntegerField())))\
        .filter(sum_approved__gte=1)

    sentences = sentences\
        .annotate(person_no_more_recording=Sum(
            Case(
                When(
                    recording__isnull=True,
                    then=Value(0)),
                When(
                    recording__person=person,
                    then=Value(-1)),
                default=Value(0),
                output_field=IntegerField())))\
        .filter(person_no_more_recording=0)

    return sentences


def get_next_sentence(request, recordings=None):
    sentences = get_sentences(request, recordings)
    if len(sentences) > 1:
        i = random.randint(0, len(sentences)-1)
        return sentences[i]
    elif len(sentences) == 1:
        return sentences[0]
    else:
        return None


def get_sentences_annonymous(request):
    current_language = get_current_language(request)
    sentences_without_recordings = Sentence.objects.filter(language=current_language, recording__isnull=True)
    return sentences_without_recordings


def get_sentence_annonymous(request):
    sentences_without_recordings = get_sentences_annonymous(request)
    return sentences_without_recordings.first()
