from django.contrib import admin

from .models import \
    License, AcceptLicense, SiteLicense


admin.site.register(License)


@admin.register(AcceptLicense)
class AcceptLicenseAdmin(admin.ModelAdmin):
    list_display = (
        'person',
        'license_names'
        )


@admin.register(SiteLicense)
class SiteLicenseAdmin(admin.ModelAdmin):
    list_display = (
        'site',
        'license'
    )
