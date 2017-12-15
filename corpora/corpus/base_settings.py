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

    # ('mi', (
    #         ('kaitahu',  _('Kaitahu')),
    #         ('muriwhen', _('Muriwhenua')),
    #         ('taranaki', _('Taranaki')),
    #         ('tuhoe', _('Tuhoe')),
    # )),

    ('mi', (
            ('tokerau', _('Te Tai Tokerau')),
            ('rawhiti', _('Te Tai Rawhiti')),
            ('hauauru', _('Te Tai Hauauru')),
            ('taitonga', _('Te Tai Tonga')),
            # ('tepuku', _('Te Puku o te Ika')),
            # ('waipouna', _('Te Waipounamu')),
    )),

)

DIALECTS_HELP_TEXT = (

    ('mi', (
            ('tokerau', _('Te Tai Tokerau')),
            ('rawhiti', _('Te Tai Rāwhiti')),
            ('hauauru', _('Te Tai Hauāuru')),
            ('taitonga', _('Te Tai Tonga')),
            # ('tepuku', _('Te Puku o te Ika')),
            # ('waipouna', _('Te Waipounamu')),
    )),


)

ACCENTS = (

    ('mi', (
            # ('academic', _('Academic')),
            # ('modern',   _('Modern')),
            # ('englishi', _('English "i"')),
    )),

    ('en', (
            ('australi', _('Australian')),
            ('newzeald', _('New Zealand')),
            ('american', _('American')),
    )),

)

LANGUAGE_CODE = 'mi'
