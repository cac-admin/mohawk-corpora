# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.utils import translation
from django.conf import settings

from corpus.base_settings import \
    LANGUAGES

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .models import Person, KnownLanguage

from allauth.account.models import EmailAddress

import logging
logger = logging.getLogger('corpora')


def get_or_create_person(request):
    user = request.user
    if user.is_anonymous:
        # Check if a session cookie exists
        uuid = request.get_signed_cookie('uuid', None)
        if uuid is not None:
            # get person from uuid
            person, created = Person.objects.get_or_create(uuid=uuid)
            if created:
                logger.info("Created new person, {0}".format(person))
        else:
            # Create person and set uuid
            person = Person.objects.create()
        request.session['uuid'] = person.uuid
    else:
        try:
            person = Person.objects.get(user=user)
        except ObjectDoesNotExist:
            uuid = request.get_signed_cookie('uuid', None)
            if uuid is not None:
                person = Person.objects.get(uuid=uuid)
                if person.user is not None:
                    if person.user is not user:
                        # Another user has signed in
                        # and this user needs a person!
                        person = Person.objects.create(user=user)
                else:
                    person.user = user
            else:
                person = Person.objects.create(user=user)
            first = '' if not user.first_name else user.first_name
            last = '' if not user.last_name else user.last_name
            if first == '' and last == '':
                full_name = user.username
            else:
                full_name = '{0} {1}'.format(first, last)
            if not person.full_name:
                person.full_name = full_name
            person.save()
        request.session['uuid'] = person.uuid

    if person:
        try:
            person.last_user_agent = request.META['HTTP_USER_AGENT']
            person.save()
        except:
            pass

    return person


def get_person(request):
    user = request.user
    if user.is_anonymous:
        # Check if a session cookie exists
        uuid = request.get_signed_cookie('uuid', None)
        if uuid is not None:
            # get person from uuid
            try:
                person = Person.objects.get(uuid=uuid)
            except ObjectDoesNotExist:
                return None
        else:
            return None
    else:
        try:
            person = Person.objects.get(user=user)
        except ObjectDoesNotExist:
            uuid = request.get_signed_cookie('uuid', None)
            if uuid is not None:
                person = Person.objects.get(uuid=uuid)
                person.user = user
            else:
                return None
            person.save()

    if person:
        try:
            person.last_user_agent = request.META['HTTP_USER_AGENT']
            person.save()
        except:
            pass

    return person


def set_language_cookie(response, language):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=2*365 * 24 * 60 * 60,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None
    )
    return response


def set_current_language_for_person(person, language):
    try:
        kl = KnownLanguage.objects.get(person=person, language=language)
        kl.active = True
        kl.save()
    except ObjectDoesNotExist:
        kl = KnownLanguage.objects.create(person=person, language=language)
        kl.active = True
        kl.save()
    translation.activate(language)


def get_current_language(request):
    language = translation.get_language()
    if request.user.is_authenticated():
        person = get_or_create_person(request)
        try:
            active_language = \
                KnownLanguage.objects.get(person=person, active=True)
            return active_language.language

        except ObjectDoesNotExist:
            return language
    else:
        return language


def get_num_supported_languages():
    return len(LANGUAGES)


def get_known_languages(person):
    if not isinstance(person, Person):
        try:
            person = Person.objects.get(user=person)
        except:
            return None
    ''' Returns a list of language codes known by person '''
    known_languages = \
        [i.language for i in KnownLanguage.objects.filter(person=person)]
    return known_languages


def get_unknown_languages(person):
    if isinstance(person, User):
        try:
            person = Person.objects.get(user=person)
        except:
            person = None
    else:
        person = None

    if person is None:
        known_languages = []
    else:
        ''' Returns a list of language codes not known by person '''
        known_languages = \
            [i.language for i in KnownLanguage.objects.filter(person=person)]

    alter_choices = []
    for i in range(len(LANGUAGES)):
        if LANGUAGES[i][0] not in known_languages:
            alter_choices.append(LANGUAGES[i][0])
    return alter_choices


def get_email(person):
    '''This method looks for and returns a verified email. If no verified email
    exists, then the next available email is returned.'''

    if person.user:
        try:
            email = EmailAddress.objects.get(user=person.user, verified=True)
            return email.email
        except ObjectDoesNotExist:
            try:
                email = EmailAddress.objects.get(user=person.user)
                return email.email
            except MultipleObjectsReturned:
                email = EmailAddress.objects.filter(user=person.user)
                if email.exists():
                    return email.email.first()
            except ObjectDoesNotExist:
                if person.user.email:
                    return person.user.email

    if person.profile_email:
        return person.profile_email
    else:
        return None


def email_verified(person):
    '''This method looks for a verified email and returns True if and only if
    1 verified email exists.'''

    if person.user:
        try:
            email = EmailAddress.objects.get(user=person.user, verified=True)
            return email.verified
        except ObjectDoesNotExist:
            try:
                email = EmailAddress.objects.get(user=person.user)
                return email.verified
            except MultipleObjectsReturned:
                return False
            except ObjectDoesNotExist:
                return False
    return False
