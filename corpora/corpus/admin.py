from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.db import models

from django.contrib import messages
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import QualityControl, Sentence, Recording, Source, Text
from corpus.views.views import RecordingFileView
from .parser import save_sentences_from_text


class QualityControlInline(GenericTabularInline):
    # max_num = 1
    extra = 0
    can_delete = False
    model = QualityControl
    raw_id_fields = ('person', 'approved_by', 'source')


class RecordingsInline(admin.TabularInline):
    extra = 0
    can_delete = False
    model = Recording
    # fields = ('sentence_text', 'duration', 'user_agent')
    raw_id_fields = ('person', 'source')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ('text', 'updated', 'content_type', 'object_id',
                    'good', 'bad', 'calculate_score',
                    'approved', 'delete', 'follow_up', 'noise', 'star')
    date_hierarchy = 'updated'
    raw_id_fields = ('person', 'approved_by')

    def text(self, obj):
        return obj.__unicode__()


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    list_display = ('text', 'updated', 'get_approved', 'get_approved_by',
                    'num_recordings')
    inlines = [QualityControlInline, RecordingsInline]
    search_fields = ['text']

    def get_queryset(self, request):
        qs = super(SentenceAdmin, self).get_queryset(request)
        qs = qs\
            .annotate(sum_approved=models.Sum(
                models.Case(
                    models.When(
                        quality_control__isnull=True,
                        then=models.Value(0)),
                    models.When(
                        quality_control__approved=True,
                        then=models.Value(1)),
                    models.When(
                        quality_control__approved=False,
                        then=models.Value(0)),
                    default=models.Value(0),
                    output_field=models.IntegerField())))
        return qs

    def get_approved(self, obj):
        return obj.sum_approved
    get_approved.short_description = 'Approvals'
    get_approved.admin_order_field = 'sum_approved'

    def get_approved_by(self, obj):
        qc = obj.quality_control
        results = qc.all()
        names = []
        if len(results) > 0:
            for r in results:
                if r.approved_by:
                    names.append(str(r.approved_by))
            return ', '.join(names)
        else:
            return _("None")
    get_approved_by.short_description = 'Approved By'
    get_approved_by.admin_order_field = 'quality_control__approved'

    def num_recordings(self, obj):
        return Recording.objects.filter(sentence=obj).count()
    num_recordings.short_description = '# Recordings'
    num_recordings.admin_order_field = 'recording__count'


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = (
        'sentence_text',
        'person',
        'get_approved',
        # 'get_approved_by',
        'calculate_score',
        'created',
    )

    inlines = [QualityControlInline]

    readonly_fields = (
        'duration',
        'audio_file',
        'audio_file_aac',
        'audio_file_admin',
        'updated',
        'created',
    )

    raw_id_fields = ('person', 'sentence')

    search_fields = [
        'person__user__email',
        'person__full_name',
        'person__user__username']

    def audio_file_aac(self, obj):
        return 'test'

    def get_queryset(self, request):
        qs = super(RecordingAdmin, self).get_queryset(request)
        qs = qs\
            .annotate(sum_approved=models.Sum(
                models.Case(
                    models.When(
                        quality_control__isnull=True,
                        then=models.Value(0)),
                    models.When(
                        quality_control__approved=True,
                        then=models.Value(1)),
                    models.When(
                        quality_control__approved=False,
                        then=models.Value(0)),
                    default=models.Value(0),
                    output_field=models.IntegerField())))
        return qs

    def get_approved(self, obj):
        return obj.sum_approved
    get_approved.short_description = 'Approvals'
    # This could be cuasing the long response for admin as it would need to
    # run this on ALL rows for sort!
    # get_approved.admin_order_field = 'sum_approved'

    def get_approved_by(self, obj):
        qc = obj.quality_control
        results = qc.all()
        names = []
        if len(results) > 0:
            for r in results:
                if r.approved_by:
                    names.append(str(r.approved_by))
            return ', '.join(names)
        else:
            return _("None")
    get_approved_by.short_description = 'Approved By'
    get_approved_by.admin_order_field = 'quality_control__approved'


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    pass


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ('uploaded_file', 'source', 'language', 'dialect',
                    'updated', )
    raw_id_fields = ('source', )
    actions = ('save_sentences', )

    def save_sentences(self, request, queryset):
        for obj in queryset:
            info = save_sentences_from_text(obj)
            messages.add_message(
                request, messages.INFO,
                '%s sentences created from %s (%s errors)' % (
                    info['saved'], obj, info['errors']))
