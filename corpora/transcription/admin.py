# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib import messages

from transcription.models import \
    Transcription, AudioFileTranscription, TranscriptionSegment

from people.helpers import get_person
from transcription.utils import create_transcription_segments_admin


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'corrected_text', 'recording')
    date_hierarchy = 'updated'
    raw_id_fields = ('recording')


@admin.register(AudioFileTranscription)
class AudioFileTranscriptionnAdmin(admin.ModelAdmin):
    actions = ('create_segments',)

    def get_changeform_initial_data(self, request):
        person = get_person(request)
        return {'uploaded_by': person.id}

    def create_segments(self, request, queryset):
        for obj in queryset:
            info = create_transcription_segments_admin(obj)
            messages.add_message(
                request, messages.INFO,
                info)


@admin.register(TranscriptionSegment)
class TranscriptionSegmentAdmin(admin.ModelAdmin):
    readonly_fields = ('start', 'end')
    list_display = ('parent', 'text', 'start', 'end')
