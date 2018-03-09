# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils.translation import ugettext as _

from django.conf import settings
from django.utils import translation, timezone
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.contenttypes.models import ContentType

from message.models import Message, MessageAction
from people.models import Person, KnownLanguage
from people.helpers import get_email, set_current_language_for_person

from celery.task.control import revoke, inspect
from django.apps import apps

from django.contrib.sites.models import Site

import datetime
import ast
import logging
logger = logging.getLogger('corpora')


@shared_task
def send_message(pk):

    try:
        ma = MessageAction.objects.get(pk=pk)
        m = ma.message
    except ObjectDoesNotExist:
        return "No message action with pk {0} exists".format(messageaction_pk)

    model = apps.get_model(
        app_label=ma.target_type.app_label,
        model_name=ma.target_type.model)
    targets = model.objects.all()

    if ma.target_id is not None:
        targets = targets.filter(pk=ma.target_id)

    if ma.target_filter:
        # try:
        query_filter = ast.literal_eval(ma.target_filter)
        targets = targets.filter(**query_filter)
        # except:
        #     return 'Error parsing query filter.'

    if ma.action in 'E':
        if 'person' in ma.target_type.model:
            for p in targets:
                send_email_to_person.apply_async(
                    args=[p.pk, m.pk, ma.pk],
                    task_id="ma-email-{0}-{1}".format(
                        p.pk, m.pk),
                    countdown=2)

        else:
            return 'Sending email to {0} not yet implemented'.format(
                ma.target_type)
    else:
        return 'Action {0} not yet implemented.'.format(ma.action)


@shared_task
def send_email_to_person(person_pk, message_pk, ma_pk):
    from corpora.email_utils import EMail

    try:
        person = Person.objects.get(pk=person_pk)
    except ObjectDoesNotExist:
        return "No person with id {0} found.".format(person_pk)

    try:
        message = Message.objects.get(pk=message_pk)
    except ObjectDoesNotExist:
        return "No message with id {0} found.".format(message_pk)

    try:
        ma = MessageAction.objects.get(pk=ma_pk)
    except ObjectDoesNotExist:
        return "No message action with id {0} found.".format(message_pk)

    # Set the language - this is used when rendering the templates.
    language = translation.get_language()
    try:
        active_language = \
            KnownLanguage.objects.get(person=person, active=True)
        language = active_language.language
    except ObjectDoesNotExist:
        pass
    translation.activate(language)

    email = get_email(person)

    if email:

        url_append = 'https://' + Site.objects.get_current().domain

        subject = message.subject

        e = EMail(to=email, subject=subject)
        context = {
            'subject': subject,
            'person': person,
            'content': message.content,
            'url_append': url_append,
            'site': Site.objects.get_current()
        }

        e.text('message/email/email_message.txt', context)
        e.html('message/email/email_message.html', context)

        if settings.DEBUG:
            p_display = email
        else:
            p_display = person_pk

        result = e.send(
            from_addr='Kōrero Māori <koreromaori@tehiku.nz>',
            fail_silently='False')
        if result == 1:
            ma.completed = True
            ma.save()
            return "Sent email to {0}".format(p_display)
        else:
            return \
                "Error sending email to {0} - {1}.".format(p_display, result)

    else:
        return "No email associated with person."
