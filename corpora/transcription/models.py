# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Transcription(models.Model):
    recording = models.ForeignKey(
        'corpus.Recording')

    text = models.CharField(
        help_text='The initial transcribed text',
        max_length=1024)

    corrected_text = models.CharField(
        help_text='The corrected text',
        max_length=1024,
        null=True,
        blank=True)

    updated = models.DateTimeField(auto_now=True)

    source = models.ForeignKey(
        'corpus.Source',
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    # Need a model to store the extra metadata from the transcription
    # But we also need the nice times info
    # meta_data = models.
    # times = words and the time the start? JSON?

    class Meta:
        pass

    # Is this still relevant?
    def clean(self):
        if len(self.text) > 124:
            raise ValidationError('Sentence too long')

        if Transcription.objects.exclude(pk=self.pk).filter(text=self.text):
            raise ValidationError('Duplicate sentence')

    def __unicode__(self):
        return self.text

    # Language and dialect should come from the recording object.
