from celery.schedules import crontab

# Will need to add "celery -A proj beat" for these to run.
# this needs to run on the webserver
# celery -A proj beat -s /webapp/logs/celery/celerybeat-schedule

CELERYBEAT_SCHEDULE = {
    'asg_launch_watchdog': {
        'task': 'transcription.tasks.launch_watcher',
        'schedule': crontab(minute='*/5'),
    },
    'transcribe_recordings_without_reviews': {
        'task': 'transcription.tasks.transcribe_recordings_without_reviews',
        'schedule': crontab(minute=53, hour='*', day_of_week='*'),
    },
    'delete_transcriptions_for_approved_recordings': {
        'task': 'transcription.tasks.delete_transcriptions_for_approved_recordings',
        'schedule': crontab(minute=23, hour='*', day_of_week='*'),
    },
}
