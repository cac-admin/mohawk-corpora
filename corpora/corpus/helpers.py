# -*- coding: utf-8 -*-

from .models import Sentence, Recording
from people.helpers import get_current_language
import random
import logging
logger = logging.getLogger('corpora')

def get_sentences(request, recordings=None):
    ''' Returns sentences without recordings '''
    current_language = get_current_language(request)
    if request.user.is_authenticated():
        if not recordings:
            recordings = Recording.objects.filter(person__user=request.user, sentence__language = current_language)
        sentences = Sentence.objects.filter(language=current_language)\
            .exclude(pk__in=[i.sentence.pk for i in recordings])\
            .exclude(quality_control__approved=False)\
            .order_by('quality_control__updated')
        return sentences
    else:
        return get_sentences_annonymous(request)    

def get_next_sentence(request, recordings=None):
    sentences = get_sentences(request, recordings)
    i = random.randint(0, len(sentences)-1)
    return sentences[i]
    

def get_sentences_annonymous(request):
    current_language = get_current_language(request)
    sentences_without_recordings = Sentence.objects.filter(language=current_language, recording__is_null=True)
    return sentences_without_recordings

def get_sentence_annonymous(request):
    sentences_without_recordings = get_sentences_annonymous(request)
    return sentences_without_recordings.first()
