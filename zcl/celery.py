from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.app.task import Task
import logging

log = logging.getLogger(__name__)
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zcl.settings')



class LoggingTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        kwargs={}
        if log.isEnabledFor(logging.DEBUG):
            kwargs['exc_info']=exc
        print('Task % failed to execute', task_id, kwargs)
        log.error('Task % failed to execute', task_id, kwargs)
        super().on_failure(exc, task_id, args, kwargs, einfo)


app = Celery('zcl', task_cls=LoggingTask)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))