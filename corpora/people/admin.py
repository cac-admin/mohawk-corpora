from django.contrib import admin

from .models import \
    Person, Demographic, KnownLanguage,\
    Tribe

from people.forms import DemographicFormAdmin

admin.site.register(Tribe)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'user',
        'uuid',
        )
    readonly_fields = ('profile_email',)


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
