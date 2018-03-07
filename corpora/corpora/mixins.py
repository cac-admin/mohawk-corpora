# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext as _


class SiteInfoMixin(object):
    x_description = _('Description for a particular view')
    x_title = _('Title for your view')

    def get_context_data(self, **kwargs):
        context = super(SiteInfoMixin, self).get_context_data(**kwargs)
        context['x_title'] = self.x_title
        context['x_description'] = self.x_description
        return context
