import os
import threading
from flask import Flask, render_template
from gevent import pywsgi
from main import UpdateSource

app = Flask(__name__, template_folder='.')


@app.route('/')
def index():
    us = UpdateSource()
    thread = threading.Thread(target=us.main)
    thread.start()
    return render_template('index.html')


@app.route('/tv')
def tv():
    if os.path.exists("result.txt"):
        return "ok"
    return "请稍候重试"

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 8989), app)
    server.serve_forever()
