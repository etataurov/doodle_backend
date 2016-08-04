from gevent import monkey
monkey.patch_all()
import os
import uuid
import flask
import datetime

from redis import Redis
from .tasks import *

from flask_oauthlib.provider import OAuth2Provider

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_client = Redis(redis_host)

app = flask.Flask(__name__)
app.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"] = 36000000000
oauth = OAuth2Provider(app)

cwd = os.path.abspath(os.path.dirname(__file__))
SAMPLES_FOLDER = os.path.join(cwd, "online_doodle_files")

# allow requests only with this token provided

# we need to keep styles somewhere
# in local json file?

CLIENT_ID = os.environ.get("CLIENT_ID") or "some_client_id"

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
    return client


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
    print("getting token")
    print(access_token)
    result = redis_client.hgetall(access_token)
    print(result)
    if result:
        expires = datetime.datetime.strptime(result[b"expires"].decode(), "%Y-%m-%d %H:%M:%S.%f")
        client_id = result[b"client_id"]
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
            style_data = STYLES[style]
            result = process_image.delay(uid, style_data["colors"], style_data["model"])
            result.get()
            return flask.jsonify(uid=uid, result_url=flask.url_for('result', filename="{}.png".format(uid)))
    flask.abort(400)
