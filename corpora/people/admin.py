from django.contrib import admin

from .models import \
    Person, Demographic, KnownLanguage,\
    Tribe, Group

from people.forms import DemographicFormAdmin
from corpus.models import Recording
admin.site.register(Tribe)


class PersonRecordingsInline(admin.StackedInline):
    model = Recording
    extra = 0
    can_delete = True
    fields = ['sentence', 'sentence_text', 'user_agent', 'audio_file_admin']
    readonly_fields = ['user_agent', 'audio_file_admin']
    raw_id_fields = ('sentence', )
    # def myaudio_file_admin(self, obj):
    #     return obj.audio_file_admin()


class PersonGroupInline(admin.TabularInline):
    model = Person.groups.through
    extra = 0
    raw_id_fields = ('group', )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'user',
        'uuid',
        'get_groups'
        )
    readonly_fields = ('profile_email',)
    inlines = [PersonRecordingsInline, PersonGroupInline]
    exclude = ('groups', )  # see PersonGroupInline

    def get_groups(self, obj):
        return ', '.join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'groups'


@admin.register(Demographic)
class DemographicAdmin(admin.ModelAdmin):
    form = DemographicFormAdmin
    list_display = (
        'person',
        'gender',
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


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'created_by', )
