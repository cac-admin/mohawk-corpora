# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from corpus.base_settings import LANGUAGES, LANGUAGE_CODE, DIALECTS, ACCENTS
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import uuid


def get_uuid():
    return str(uuid.uuid4())


class Tribe(models.Model):
    name = models.CharField(
        help_text=_('Name of tribe.'),
        max_length=200,
        unique=True)

    class Meta:
        verbose_name = _('Tribe')
        verbose_name_plural = _('Tribes')

    def __unicode__(self):
        return self.name


class Person(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    full_name = models.CharField(
        help_text=_('Full Name'),
        max_length=200,
        blank=True)
    uuid = models.CharField(
        max_length=64,
        default=get_uuid,
        editable=False,
        unique=True)
    # accept_terms = models.BooleanField(editable=False, default=False)

    def email(self):
        if self.user:
            return self.user.email

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('People')

    def __unicode__(self):
        return self.full_name


class Demographic(models.Model):
    SEX_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('TF', _('Transexual (Male to Female)')),
        ('TM', _('Transexual (Female to Male)')),
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('How old are you?'))
    sex = models.CharField(
        help_text=_('Gender'),
        choices=SEX_CHOICES,
        max_length=2,
        null=True,
        blank=True)
    person = models.OneToOneField(
        Person,
        related_name='demographic',
        on_delete=models.CASCADE,
        null=True,
        unique=True)

    tribe = models.ManyToManyField(
        Tribe,
        help_text=_('Which tribe(s) do you identify with?'),
        null=True,
        blank=True)
    # tribe - This should be many field - many to many?
    # where did you grow up
    # ethnicities
    # anthing else?

    def tribe_names(self):
        return u', '.join([a.name for a in self.tribe.all()])
    tribe_names.short_description = _('Tribes')


class KnownLanguage(models.Model):
    PROFICIENCIES = (
            (1, _('Native Speaker - Beginner')),
            (2, _('Native Speaker - Intermediate')),
            (3, _('Native Speaker - Advanced')),
            (4, _('Near Native Speaker - Beginner')),
            (5, _('Near Native Speaker - Intermediate')),
            (6, _('Near Native Speaker - Advanced')),
            (7, _('Second Language Learner - Beginner')),
            (8, _('Second Language Learner - Intermediate')),
            (9, _('Second Language Learner - Advanced')),
        )

    language = models.CharField(choices=LANGUAGES, max_length=16)
    level_of_proficiency = models.IntegerField(
        choices=PROFICIENCIES,
        null=True,
        blank=True)

    person = models.ForeignKey(
        Person,
        related_name='known_languages',
        on_delete=models.CASCADE)

    active = models.BooleanField(default=False)

    accent = models.CharField(choices=ACCENTS, max_length=8, null=True)
    dialect = models.CharField(choices=DIALECTS, max_length=8, null=True)
    # where did you learn your reo?

    class Meta:
        unique_together = (('person', 'language'))


@receiver(models.signals.post_save, sender=KnownLanguage)
def deactivate_other_known_languages_when_known_language_activated(
        sender,
        instance,
        **kwargs):

    if instance.active:
        known_languages = KnownLanguage.objects\
            .filter(person=instance.person)\
            .exclude(pk=instance.pk)

        for kl in known_languages:
            kl.active = False
            kl.save()


@receiver(models.signals.post_save, sender=KnownLanguage)
def ensure_a_language_is_active(sender, instance, **kwargs):
    try:
        active_language = KnownLanguage.objects.get(
            person=instance.person,
            active=True)
    except ObjectDoesNotExist:
        known_language = KnownLanguage.objects\
            .filter(person=instance.person).first()

        if known_language:
            known_language.active = True
            known_language.save()


@receiver(models.signals.post_delete, sender=KnownLanguage)
def change_active_language_when_active_language_deleted(
        sender, instance, **kwargs):

    if instance.active:
        known_language = KnownLanguage.objects\
            .filter(person=instance.person).first()

        if known_language:
            known_language.active = True
            known_language.save()
