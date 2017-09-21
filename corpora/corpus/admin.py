from django.contrib import admin

# Register your models here.

from .models import QualityControl, Sentence, Recording

admin.site.register(QualityControl)
admin.site.register(Sentence)
admin.site.register(Recording)
