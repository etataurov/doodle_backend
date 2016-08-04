import os
from celery import Celery
import time

url = os.environ.get("RABBIT_URL") or 'amqp://guest@localhost//'

app = Celery('doodle_backend.tasks', broker=url)
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERY_RESULT_SERIALIZER = 'json'
app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_RESULT_BACKEND = url


@app.task
def add(x, y):
    time.sleep(10)
    return x + y
