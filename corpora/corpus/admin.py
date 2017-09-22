from django.contrib import admin
from django.db import models

from django.contrib.contenttypes.admin import GenericTabularInline

# Register your models here.

from .models import QualityControl, Sentence, Recording


class QualityControlInline(GenericTabularInline):
    max_num = 1
    can_delete = False
    model = QualityControl


class RecordingsInline(admin.TabularInline):
    extra = 0
    can_delete = False
    model = Recording


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ('updated', 'content_type',)
    date_hierarchy = 'updated'


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    list_display = ('text', 'updated', 'get_approved', 'get_approved_by', 'num_recordings')
    inlines = [QualityControlInline, RecordingsInline]

    def get_queryset(self, request):
        qs = super(SentenceAdmin, self).get_queryset(request)
        qs = qs.annotate(models.Count('recording'))
        return qs

    def get_approved(self, obj):
        qc = obj.quality_control
        return qc.all()[0].approved
    get_approved.short_description = 'Approved'
    get_approved.admin_order_field = 'quality_control__approved'

    def get_approved_by(self, obj):
        qc = obj.quality_control
        return qc.all()[0].approved_by
    get_approved_by.short_description = 'Approved'
    get_approved_by.admin_order_field = 'quality_control__approved'

    def num_recordings(self, obj):
        return obj.recording__count
    num_recordings.short_description = '# Recordings'
    num_recordings.admin_order_field = 'recording__count'


admin.site.register(Recording)
