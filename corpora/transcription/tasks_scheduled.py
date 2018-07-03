from celery.schedules import crontab

# Will need to add "celery -A proj beat" for these to run.
# this needs to run on the webserver
# celery -A proj beat -s /webapp/logs/celery/celerybeat-schedule

CELERYBEAT_SCHEDULE = {
    'asg_launch_watchdog': {
        'task': 'transcription.tasks.launch_watcher',
        'schedule': crontab(minute='*/5'),
    },
}
