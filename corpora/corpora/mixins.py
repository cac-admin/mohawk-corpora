# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext as _
from django.contrib.sites.shortcuts import get_current_site


class SiteInfoMixin(object):
    x_description = _('Description for a particular view')
    x_title = _('Title for your view')
    x_image = ""

    def get_context_data(self, **kwargs):
        context = super(SiteInfoMixin, self).get_context_data(**kwargs)
        context['x_title'] = self.x_title
        context['x_description'] = self.x_description

        if 'http' not in self.x_image:
            site = get_current_site(self.request)
            self.x_image = 'https://'+site.domain + self.x_image

        context['x_image'] = self.x_image
        return context
