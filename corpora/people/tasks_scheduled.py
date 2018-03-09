from celery.schedules import crontab

# Will need to add "celery -A proj beat" for these to run.
# this needs to run on the webserver
# celery -A proj beat -s /webapp/logs/celery/celerybeat-schedule

CELERYBEAT_SCHEDULE = {
    'clean_empty_person_models': {
        'task': 'people.tasks.clean_empty_person_models',
        'options': {'task_id': 'clean_empty_person_models'},
        'schedule': crontab(minute='*/5', hour='*', day_of_week='*'),
        'relative': True,
    },
    'clean_empty_group_models': {
        'task': 'people.tasks.clean_empty_group_models',
        'options': {'task_id': 'clean_empty_group_models'},
        'schedule': crontab(minute='*/20', hour='*', day_of_week='*'),
        'relative': True,
    },
    'send_person_weekly_emails': {
        'task': 'people.tasks.send_person_emails',
        'kwargs': {'frequency': 'weekly'},
        'options': {'task_id': 'send_person_weekly_emails'},
        'schedule': crontab(minute='0', hour='9', day_of_week='tuesday'),
    },
    'send_person_daily_emails': {
        'task': 'people.tasks.send_person_emails',
        'kwargs': {'frequency': 'daily'},
        'options': {'task_id': 'send_person_daily_emails'},
        'schedule': crontab(minute='10', hour='12', day_of_week='*'),
    },
    # 'calculate_person_scores': {
    #     'task': 'people.tasks.calculate_person_scores',
    #     'schedule': crontab(minute='12,32,52', hour='*', day_of_week='*'),
    # },
    # 'calculate_group_scores': {
    #     'task': 'people.tasks.calculate_group_scores',
    #     'schedule': crontab(minute='12,32,52', hour='*', day_of_week='*'),
    # },
}
