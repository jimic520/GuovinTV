FROM python:3.8
# 将 Dockerfile 所在的目录设置为工作目录
WORKDIR /app

# 复制 requirements.txt 文件到镜像中
COPY requirements.txt .

RUN pip install requests feedparser pytz aiohttp bs4 tqdm async-timeout Flask Flask-SocketIO gunicorn gevent

# 将 Dockerfile 所在目录下的所有文件复制到镜像中的 /app 目录下
COPY . .
EXPOSE 8989
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:8989", "app:app"]
