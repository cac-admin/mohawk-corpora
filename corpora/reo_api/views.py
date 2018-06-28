# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.shortcuts import render

from django.views.generic.base import TemplateView
from corpora.mixins import SiteInfoMixin

from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.documentation import get_docs_view
from rest_framework.renderers import (
    CoreJSONRenderer, DocumentationRenderer, SchemaJSRenderer
)
from rest_framework.schemas import SchemaGenerator, get_schema_view
from rest_framework import authentication, permissions
from rest_framework.schemas import AutoSchema
from rest_framework.response import Response

import logging
logger = logging.getLogger('corpora')


class HomeView(SiteInfoMixin, TemplateView):
    template_name = "reo_api/home.html"
    x_title = _('kōreromāori.io')
    x_description = _('Indigenous language tools powered by machine learning.')


class DocsDashboardView(SiteInfoMixin, TemplateView):
    template_name = "reo_api/docs.html"
    x_title = _('Documentation')
    x_description = _('API documentation.')


class BrowseAPIDashboardView(SiteInfoMixin, TemplateView):
    template_name = "reo_api/api_browse.html"
    x_title = _('Browseable API')
    x_description = _('Browseable API.')
