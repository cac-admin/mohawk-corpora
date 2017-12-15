from license.models import SiteLicense
from django.conf import settings


def license(request):
    try:
        license = SiteLicense.objects.get(site=settings.SITE_ID)
        return {'license': license.license}
    except:
        return {}
