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
MOUNT_FOLDER = ""


@app.task
def add(x, y):
    time.sleep(10)
    return x + y


@app.task
def process_image(item_id, colors, model):
    subprocess.call(["nvidia-docker", "run", "-v",
                     "/data/repos/online-neural-doodle/:/root/data",
                     "-v",
                     "/data/repos/doodle_web/online_doodle_files:/root/doodle/",
                     "conv_image", "apply.py",
                     "--colors", "/root/data/" + colors,
                     "--target_mask",
                     os.path.join(MOUNT_FOLDER, "{}_mask.png".format(item_id)),
                     "--model", "/root/data/" + model,
                     "--out_path",
                     os.path.join(MOUNT_FOLDER, "{}.png".format(item_id))],
                    cwd=os.path.join(cwd, os.pardir))
