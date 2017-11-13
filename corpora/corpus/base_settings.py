# -*- coding: utf-8 -*-

import django.conf.locale
from django.utils.translation import ugettext_lazy as _

EXTRA_LANG_INFO = {
    'mi': {
        'bidi': False,  # right-to-left
        'code': 'mi',
        'name': 'Maori',
        'name_local': u'Māori',
    },
    'en_NZ': {
        'bidi': False,  # right-to-left
        'code': 'en_NZ',
        'name': 'New Zealand English',
        'name_local': u'New Zealand English',
    },
}

LANG_INFO = \
    dict(django.conf.locale.LANG_INFO.items() + EXTRA_LANG_INFO.items())

# update the language info
django.conf.locale.LANG_INFO = LANG_INFO


LANGUAGE_COOKIE_NAME = 'corpora-language'
# LOCALE_PATHS = (
# We're making a local directory in each app and the project-app folder
#     os.path.join(BASE_DIR, 'locale'),
# )

LANGUAGES = (

    ('mi',    _('Maori')),
    # ('en',    _('English')),
    # ('en_NZ', _('New Zealand English')),

)

DIALECTS = (

    ('mi', (
            ('muriwhen', _('Muriwhenua')),
            ('kaitahu',  _('Kaitahu')),
            ('taranaki', _('Taranaki')),
    )),

)

ACCENTS = (

    ('mi', (
            ('academic', _('Academic')),
            ('modern',   _('Modern')),
            ('englishi', _('English "i"')),
    )),

)

LANGUAGE_CODE = 'mi'
