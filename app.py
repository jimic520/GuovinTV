import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from main import UpdateSource

app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return render_template('./index.html')


@socketio.on('connect')
def handle_connect():
    # 在连接时处理逻辑
    print("connected")


@socketio.on('tv_task')
def handle_tv_task():
    # 模拟长时间任务
    print("do task")
    # socketio.emit('server_message', {'message': 'txt'})
    UpdateSource().main()
    if os.path.exists('result.txt'):
        with open('result.txt', 'r', encoding='utf-8') as f:
            txt = f.read()
            emit('server_message', {'message': txt})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8989, debug=False)
