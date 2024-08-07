from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xloserver.settings')

app = Celery('xloserver')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['apps.blog', 'apps.base'])

app.conf.beat_schedule = {
    'send_weekly_recall_email_9am': {
        'task': 'apps.blog.tasks.send_weekly_recall_email',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}
