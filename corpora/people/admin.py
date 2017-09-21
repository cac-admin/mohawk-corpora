from django.contrib import admin

from .models import Person, Demographic, KnownLanguage

admin.site.register(Person)
admin.site.register(Demographic)
admin.site.register(KnownLanguage)
