# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey,\
                                               GenericRelation
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from corpora.settings import LANGUAGES, LANGUAGE_CODE

from uuid import uuid4


def upload_directory(instance, filename):
    d = timezone.now()
    i = str(uuid4())
    return '{0}/{1}.{2}'.format(
        d.strftime('%Y/%m/%d/%H/%M'),
        i,
        filename.split('.')[-1])


class QualityControl(models.Model):
    good = models.PositiveIntegerField(default=0)
    bad = models.PositiveIntegerField(default=0)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("object_id", "content_type"),)

    def __unicode__(self):
        return "{0}:{1}:{2}".format(
            self.content_type, self.object_id, self.good-self.bad)

    def clear(self):
        self.good = 0
        self.bad = 0
        self.approved = False
        self.approved_by = None


class Sentence(models.Model):
    text = models.CharField(help_text='The sentence to be spoken.',
                            max_length=250, unique=True)
    language = models.CharField(choices=LANGUAGES,
                                max_length=16,
                                default=LANGUAGE_CODE)
    quality_control = GenericRelation(QualityControl, related_query_name='sentence')
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sentence'
        verbose_name_plural = 'Sentences'

    def __unicode__(self):
        return self.text


class Recording(models.Model):
    person = models.ForeignKey('people.Person')
    sentence = models.ForeignKey('Sentence')
    audio_file = models.FileField(upload_to=upload_directory)
    quality_control = GenericRelation(QualityControl, related_query_name='recording')
    updated = models.DateTimeField(auto_now=True)
    sentence_text = models.CharField(max_length=250, blank=True, null=True)
    duration = models.FloatField(default=0, blank=True)

    class Meta:
        verbose_name = 'Recording'
        verbose_name_plural = 'Recordings'
        unique_together = (("person", "sentence"),)

    def __unicode__(self):
        return self.sentence.text + " by " + self.person.full_name

    def get_recording_file_url(self):
        from django.urls import reverse
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        return "https://{1}{0}".format(
            reverse('corpus:recording_file', kwargs={'pk': self.pk}),
            current_site.domain)
