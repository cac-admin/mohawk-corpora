from django.contrib import admin

# Register your models here.

from .models import QualityControl, Sentence, Recording


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ('updated', 'content_type',)
    date_hierarchy = 'updated'


admin.site.register(Sentence)
admin.site.register(Recording)
