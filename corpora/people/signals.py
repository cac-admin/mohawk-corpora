# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.dispatch import receiver
from allauth.account import signals

from .models import Person
from .helpers import get_or_create_person


@receiver(signals.user_signed_up)
def user_signed_ip(request, user, **kwargs):
    request.user = user
    person = get_or_create_person(request)
    person.just_signed_up = True
    person.save()
