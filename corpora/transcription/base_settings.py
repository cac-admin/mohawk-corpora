# -*- coding: utf-8 -*-
import os

FILE_UPLOAD_PERMISSIONS = 0644

# This isn't set up anymore. This was really for local development
DEEPSPEECH_URL_PUBLIC = \
    "http://deep.koreromaori.io/transcribe"

# This is no longer "private" we have it on a application LBB bbut only certain
# security groups and IPs can access this LBB.
DEEPSPEECH_URL_PRIVATE = \
    "LB-corpora-production-deepspeech-1243053555.ap-southeast-2.elb.amazonaws.com/transcribe"


if 'local' in os.environ['ENVIRONMENT_TYPE']:
    DEEPSPEECH_URL = DEEPSPEECH_URL_PUBLIC
else:
    DEEPSPEECH_URL = DEEPSPEECH_URL_PRIVATE

OLD_URL = "http://waha-tuhi-api-17.dragonfly.nz/transcribe"