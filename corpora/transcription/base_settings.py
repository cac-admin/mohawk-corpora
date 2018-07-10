# -*- coding: utf-8 -*-

FILE_UPLOAD_PERMISSIONS = 0644

DEEPSPEECH_URL_PUBLIC = \
    "http://deep.koreromaori.io/transcribe"

DEEPSPEECH_URL_PRIVATE = \
    "http://LB-corpora-production-deep-tcp-4113e81f0772e13a.elb.ap-southeast-2.amazonaws.com"

if 'local' in os.environ['ENVIRONMENT_TYPE']:
    DEEPSPEECH_URL = DEEPSPEECH_URL_PUBLIC
else:
    DEEPSPEECH_URL = DEEPSPEECH_URL_PRIVATE

OLD_URL = "http://waha-tuhi-api-17.dragonfly.nz/transcribe"