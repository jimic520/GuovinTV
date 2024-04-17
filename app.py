import os
import threading
from flask import Flask, g
from gevent import pywsgi
from main import UpdateSource

try:
    import user_config as config
except ImportError:
    import config

app = Flask(__name__)

app.config['run_thread'] = None

@app.route('/')
def index():
    us = UpdateSource().main()
    return redirect('/tv')


@app.route('/tv')
def tv():
    user_final_file = getattr(config, "final_file", "result.txt")
    if os.path.exists(user_final_file):
        with open(user_final_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "结果还未生成，请稍候..."


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 8989), app)
    server.serve_forever()
