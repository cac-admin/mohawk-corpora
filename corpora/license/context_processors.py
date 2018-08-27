from license.models import SiteLicense
from django.contrib.sites.shortcuts import get_current_site


def license(request):
    try:
        license = SiteLicense.objects.get(site=get_current_site(request))
        return {'license': license.license}
    except:
        return {}
