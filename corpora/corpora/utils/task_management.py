from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.core.cache import cache


def check_and_set_task_running(task_id):
    key = u"task-{0}-isrunning".format(task_id)
    is_running = cache.get(key, False)
    if is_running:
        return True
    else:
        cache.set(key, True)
        return False


def clear_running_tasks(task_id):
    key = u"task-{0}-isrunning".format(task_id)
    cache.delete(key)
