# -*- coding: utf-8 -*-

from django.utils import translation
from django.conf import settings
from people.helpers import get_current_language, get_or_create_person
from license.models import SiteLicense


class PersonMiddleware(object):
    '''
    This middleware sets a uuid cookie so we can collect data immidiately
    without users signing in. it also allows us to later associate the
    uuid with a user account when/if the user creates an account.
    '''

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        person = get_or_create_person(request)
        response = self.get_response(request)
        response.set_signed_cookie(
                'uuid',
                person.uuid,
                max_age=365 * 24 * 60 * 60,
                domain=settings.SESSION_COOKIE_DOMAIN,
                secure=settings.SESSION_COOKIE_SECURE or None
            )
        # Code to be executed for each request/response after
        # the view is called.
        return response


class LanguageMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        set_cookie = False
        if request.COOKIES.has_key(settings.LANGUAGE_COOKIE_NAME):
            language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        elif hasattr(request,'user'):
            if request.user.is_authenticated():
                current_language = get_current_language(request)
                if current_language:
                    set_cookie = True
        else:
            language = translation.get_language()
            # set_cookie = True

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        response = self.get_response(request)

        if set_cookie:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language,
                max_age=2*365 * 24 * 60 * 60, 
                domain=settings.SESSION_COOKIE_DOMAIN, 
                secure=settings.SESSION_COOKIE_SECURE or None
            )


        # Code to be executed for each request/response after
        # the view is called.

        translation.deactivate() # Deactivates our langauge after we've processed the request.
        return response


class LicenseMiddleware(object):
    '''
    This middleware sets the license of the current site.
    '''

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        try:
            license = SiteLicense.objects.get(site=settings.SITE_ID)
        except:
            license = None

        request.license = license

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
