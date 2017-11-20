from celery.schedules import crontab

# Will need to add "celery -A proj beat" for these to run.
# this needs to run on the webserver
# celery -A proj beat -s /webapp/logs/celery/celerybeat-schedule

CELERYBEAT_SCHEDULE = {
    'clean_empty_person_models': {
        'task': 'people.tasks.clean_empty_person_models',
        'schedule': crontab(minute='*/5', hour='*', day_of_week='*'),
    },
}
