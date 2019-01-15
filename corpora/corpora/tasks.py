from __future__ import absolute_import, unicode_literals
from celery import shared_task

from corpora.utils.tmp_files import erase_all_temp_files

import logging
logger = logging.getLogger('corpora')
logger_test = logging.getLogger('django.test')


@shared_task
def erase_all_temp_files():
    try:
        erase_all_temp_files(None)
        return "Erased all temp files."
    except:
        return "Error erasing all temp files."
