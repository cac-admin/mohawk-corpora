from django.contrib import admin

from .models import \
    Person, Demographic, KnownLanguage,\
    License, AcceptLicense, Tribe

from people.forms import DemographicFormAdmin

admin.site.register(Person)
admin.site.register(License)
admin.site.register(Tribe)


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


@admin.register(AcceptLicense)
class AcceptLicenseAdmin(admin.ModelAdmin):
    list_display = (
        'person',
        'license_names'
        )
