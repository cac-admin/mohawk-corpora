# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.shortcuts import render

from django.views.generic.base import TemplateView
from corpora.mixins import SiteInfoMixin


class HomeView(SiteInfoMixin, TemplateView):
    template_name = "reo_api/home.html"
    x_title = _('kōreromāori.io')
    x_description = _('Indigenous language tools powered by machine learning.')
