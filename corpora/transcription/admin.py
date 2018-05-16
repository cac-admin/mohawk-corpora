# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from transcription.models import Transcription


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'corrected_text', 'recording')
    date_hierarchy = 'updated'
