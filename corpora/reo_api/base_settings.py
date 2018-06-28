# -*- coding: utf-8 -*-
import os

SITE_ID = 2

ALLOWED_HOSTS = "*"  #['{0}'.format(i) for i in os.environ['ALLOWED_HOSTS_2'].split(' ')]

ROOT_URLCONF = 'reo_api.urls'
LANGUAGE_CODE = 'en'


LOGIN_REDIRECT_URL = "/dashboard"

X_FRAME_OPTIONS = 'ALLOW-FROM koreromaori.com koreromaori.io dev.koreromaori.com dev.koreromaori.io corporalocal.io'