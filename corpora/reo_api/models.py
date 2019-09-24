# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from people.models import Person
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create your models here.


class UserAPI(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE)

    # person = models.OneToOneField(
    #     Person,
    #     on_delete=models.CASCADE)

    # token = models.OneToOneField(
    #     Token,
    #     on_delete=models.CASCADE)

    enabled = models.BooleanField(default=False)


    def token(self):
        token, created = Token.objects.get_or_create(user=self.user)
        return token

    def person(self):
        return Person.objects.get(user=self.user)

    def __str__(self):
        return str(self.user)
    
    def __unicode__(self):
        return str(self.user)

# class ApplicationAPI(Token):
#     name = models.CharField(max_length=256)

