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


class CustomDocsView(APIView):
    """
    A view that returns the count of active users in JSON.
    """
    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.BasicAuthentication)
    permission_classes = (
        permissions.IsAuthenticated,)

    renderer_classes = (DocumentationRenderer, CoreJSONRenderer)
    # generator = SchemaGenerator(title='Flight Search API')
    # # schema = AutoSchema(get_docs_view())
    # # doc_view = get_docs_view()
    # # schema = doc_view.as_view().get_schema()
    # schema = generator.get_schema()
    from rest_framework import routers
    from transcription.views import api as transcription_api
    router = routers.DefaultRouter()
    router.register(
        r'transcription-segment', transcription_api.TranscriptionSegmentViewSet)
    router.register(
        r'transcription', transcription_api.AudioFileTranscriptionViewSet)
    docs_patterns = router.urls
    logger.debug(docs_patterns)
    docs_view = get_docs_view(
        title='koreromaori.io',
        schema_url='/api/',
        patterns=docs_patterns,
        )
    schema = docs_view.func_dict['view_initkwargs']['schema_generator'].get_schema()
    logger.debug("TYPE IF SCHEME:")
    logger.debug(type(schema))

    # def get(self, request, format=None):
    #     # r = super(CustomDocsView, self).get(self, request, format=None)

        
    #     # return r
    #     return Response({
    #         'content': 'content'})
