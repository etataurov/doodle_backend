from gevent import monkey
monkey.patch_all()
import os
import flask
from .tasks import *

app = flask.Flask(__name__)
cwd = os.path.abspath(os.path.dirname(__file__))
SAMPLES_FOLDER = os.path.join(cwd, "online_doodle_files")

# allow requests only with this token provided

# we need to keep styles somewhere
# in local json file?

STYLES = {
    "monet": {
        "original": "monet.jpg",
        "annotation": "monet_mask.jpg",
        "colors": "data/monet/gen_doodles.hdf5_colors.npy",
        "model": "data/monet/model.t7",
        "name": "Monet"
    },
    "van_gogh": {
        "original": "van_gogh.png",
        "annotation": "van_gogh_mask.png",
        "colors": "pretrained/gen_doodles.hdf5colors.npy",
        "model": "pretrained/starry_night.t7",
        "name": "Van Gogh"
    },
    "agay_bay": {
        "original": "agay-bay-1910.jpg",
        "annotation": "agay-bay-1910-mask.jpegg",
        "colors": "data/agay_bay/gen_doodles.hdf5_colors.npy",
        "model": "data/agay_bay/model.t7",
        "name": "Agay Bay"
    }
}


@app.route("/list")
def list_styles():
    result = []
    for key, value in STYLES.items():
        result.append({
            "key": key,
            "name": value["name"],
            "original": flask.url_for('original_picture', style=key)
        })
    return flask.jsonify({"items": result})


@app.route('/picture/<style>.png')
def original_picture(style):
    return flask.send_from_directory(SAMPLES_FOLDER,
                                     STYLES[style]["original"])


@app.route('/task')
def perform_taks():
    result = add.delay(4, 4)
    return str(result.get())
