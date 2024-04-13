import os

from flask import Flask, render_template
from gevent import pywsgi
from main import UpdateSource

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('./index.html')



if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 8989), app)
    server.serve_forever()
