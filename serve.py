from doodle_backend import app
from gevent import wsgi

if __name__ == '__main__':
    print("started")
    server = wsgi.WSGIServer(('0.0.0.0', 5000), app.app)
    server.serve_forever()
