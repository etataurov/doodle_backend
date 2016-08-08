from gevent import monkey
monkey.patch_all()
import os
import json
import uuid
import flask
import datetime

from redis import Redis
from .tasks import *

from flask_oauthlib.provider import OAuth2Provider

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_client = Redis(redis_host, decode_responses=True)

app = flask.Flask(__name__)
app.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"] = 3600000
oauth = OAuth2Provider(app)

cwd = os.path.abspath(os.path.dirname(__file__))
SAMPLES_FOLDER = os.path.join(cwd, "../online_doodle_files")

MODELS_FOLDER = os.path.join(cwd, "../models")


CLIENT_ID = os.environ.get("CLIENT_ID") or "some_client_id"

STYLES_KEY = "doodle_styles"


def get_style_data():
    global STYLES
    if redis_client.exists(STYLES_KEY):
        result = {}
        styles = redis_client.lrange(STYLES_KEY, 0, -1)
        for style in styles:
            result[style] = redis_client.hgetall(style)
        return result
    else:
        with open(os.path.join(cwd, "initial.json")) as initial:
            result = json.load(initial)
            styles = []
            for key, value in result.items():
                styles.append(key)
                redis_client.hmset(key, value)
            redis_client.lpush(STYLES_KEY, *styles)
            return result


class Client:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.user = ""
        self.default_redirect_uri = ""
        self.allowed_grant_types = ["client_credentials"]
        self.default_scopes = ["default"]

client = Client()


@oauth.clientgetter
def load_client(client_id):
    if client_id == CLIENT_ID:
        return client
    return None


@oauth.grantgetter
def load_grant(client_id, code):
    return True


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    return True


class Token:
    def __init__(self, client_id, expires):
        self.expires = expires
        self.scopes = ["default"]
        self.user = None


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    result = redis_client.hgetall(access_token)
    if result:
        expires = datetime.datetime.strptime(result["expires"], "%Y-%m-%d %H:%M:%S.%f")
        client_id = result["client_id"]
        return Token(client_id=client_id, expires=expires)
    return None


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    expires_in = token.get('expires_in')
    expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    access_token = token.get("access_token")
    client_id = request.client.client_id
    redis_client.hmset(access_token, {"client_id": client_id, "expires": expires})
    return Token(client_id=client_id, expires=expires)


@app.route('/oauth/token')
@oauth.token_handler
def access_token():
    return None

@app.route("/api/styles")
@oauth.require_oauth('default')
def list_styles():
    result = []
    for key, value in get_style_data().items():
        result.append({
            "key": key,
            "name": value["name"],
            "original": flask.url_for('original_picture', style=key)
        })
    return flask.jsonify({"items": result})


@app.route('/picture/<style>.png')
def original_picture(style):
    return flask.send_from_directory(SAMPLES_FOLDER,
                                     get_style_data()[style]["original"])


@app.route('/result/<filename>')
def result(filename):
    return flask.send_from_directory(SAMPLES_FOLDER, filename)


@app.route("/api/process_image", methods=["POST"])
@oauth.require_oauth('default')
def process_handler():
    if flask.request.method == 'POST':
        file = flask.request.files['image']
        style = flask.request.form.get("style")
        if file:
            uid = str(uuid.uuid4())
            filename = uid + "_mask.png"
            file.save(os.path.join(SAMPLES_FOLDER, filename))
            style_data = get_style_data()[style]
            result = process_image.delay(uid, style_data["colors"], style_data["model"])
            result.get()
            return flask.jsonify(uid=uid, result_url=flask.url_for('result', filename="{}.png".format(uid)))
    flask.abort(400)


@app.route("/admin/newstyle", methods=["GET", "POST"])
def add_newstyle():
    if flask.request.method == "GET":
        return flask.render_template("add_style.html")
    else:
        try:
            original = flask.request.files["original"]
            mask = flask.request.files["mask"]
            name = flask.request.form["name"]
            key = flask.request.form["key"]
        except Exception:
            flask.abort(400, "Some fields are missing")
            return
        if redis_client.exists(key):
            flask.abort(409, "'{}' already used".format(key))
            return
        original_filename = key + ".png"
        mask_filename = key + "_mask.png"
        original.save(os.path.join(MODELS_FOLDER, original_filename))
        mask.save(os.path.join(MODELS_FOLDER, mask_filename))
        result = train_image.delay(original_filename, mask_filename, key, name)
        return flask.redirect(flask.url_for('style_status', task_id=result.id))


@app.route("/admin/style_status/<task_id>")
def style_status(task_id):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    if result.successful():
        return "Ready"
    elif result.failed():
        return "Error, {}".format(result.result)
    else:
        return "Pending"
