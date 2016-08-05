import os
from celery import Celery
import time
import subprocess

url = os.environ.get("RABBIT_URL") or 'amqp://guest@localhost//'

app = Celery('doodle_backend.tasks', broker=url)
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERY_RESULT_SERIALIZER = 'json'
app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_RESULT_BACKEND = url


cwd = ""
MOUNT_FOLDER = "/root/doodle/"


@app.task
def add(x, y):
    time.sleep(10)
    return x + y


@app.task
def process_image(item_id, colors, model):
    subprocess.call(["nvidia-docker", "run", "--rm", "-v",
                     "/data/mounted/models/:/root/data",
                     "-v",
                     "/data/mounted/online_doodle_files:/root/doodle/",
                     "conv_image2", "apply.py",
                     "--colors", "/root/data/" + colors,
                     "--target_mask",
                     os.path.join(MOUNT_FOLDER, "{}_mask.png".format(item_id)),
                     "--model", "/root/data/" + model,
                     "--out_path",
                     os.path.join(MOUNT_FOLDER, "{}.png".format(item_id))])
