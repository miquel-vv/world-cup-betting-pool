import os
import django
from celery import Celery
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wc2018.settings")
django.setup()

app = Celery('proj')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'add-every-two-hours-crontab': {
        'task': 'update_scores',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (),
    },
    # 'add-every-minute-crontab': {
    #     'task': 'test',
    #     'schedule': crontab(),
    #     'args': (5, 5),
    # },
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
