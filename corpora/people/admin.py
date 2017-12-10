from django.contrib import admin

from .models import \
    Person, Demographic, KnownLanguage,\
    Tribe

from people.forms import DemographicFormAdmin
from corpus.models import Recording
admin.site.register(Tribe)


class PersonRecordingsInline(admin.StackedInline):
    model = Recording
    extra = 0
    can_delete = False
    fields = ['sentence', 'sentence_text', 'user_agent', 'audio_file_admin']
    readonly_fields = ['user_agent', 'audio_file_admin']

    # def myaudio_file_admin(self, obj):
    #     return obj.audio_file_admin()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'user',
        'uuid',
        )
    readonly_fields = ('profile_email',)
    inlines = [PersonRecordingsInline]


@admin.register(Demographic)
class DemographicAdmin(admin.ModelAdmin):
    form = DemographicFormAdmin
    list_display = (
        'person',
        'sex',
        'age',
        'tribe_names')


@admin.register(KnownLanguage)
class KnownLanguageAdmin(admin.ModelAdmin):
    list_display = (
        'person',
        'language',
        'level_of_proficiency',
        'dialect',
        'accent',
        )
