import os
from celery import Celery
import time
import subprocess
from redis import Redis

url = os.environ.get("RABBIT_URL") or 'amqp://guest@localhost//'

app = Celery('doodle_backend.tasks', broker=url)
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERY_RESULT_SERIALIZER = 'json'
app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_RESULT_BACKEND = url
app.conf.CELERY_ROUTES = {'doodle_backend.tasks.train_image': {'queue': 'train'}}


cwd = ""
MOUNT_FOLDER = "/root/doodle/"

redis_client = Redis()

@app.task
def add(x, y):
    time.sleep(10)
    return x + y


@app.task
def process_image(item_id, colors, model):
    subprocess.check_call(["nvidia-docker", "run", "--rm", "-v",
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
    return "ok"


@app.task
def train_image(image, mask, key, name):
    subprocess.check_call(["nvidia-docker", "run", "--rm", "-v",
                     "/data/mounted/models/:/root/data",
                     "-v",
                     "/data/mounted/online_doodle_files:/root/doodle/",
                     "train_network", key])
    redis_client.rpush("doodle_styles", key)
    redis_client.hmset(key, {"original": image,
                             "annotation": mask,
                             "colors": "data/monet/gen_doodles.hdf5_colors.npy",
                             "model": "data/monet/model.t7",
                             "name": name})
    return "ok"