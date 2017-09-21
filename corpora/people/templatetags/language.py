
from django import template

from people.helpers import get_current_language as get_cur_lang
from people.helpers import get_known_languages as get_known_lang

import logging
logger = logging.getLogger('corpora')

register = template.Library()

@register.simple_tag()
def get_current_language(request):
    l = get_cur_lang(request)
    return l

@register.simple_tag()
def get_known_languages(request):
    kl = get_known_lang(request.user)
    return kl

