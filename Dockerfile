FROM python:3.8
# 将 Dockerfile 所在的目录设置为工作目录
WORKDIR /app

# 复制 requirements.txt 文件到镜像中
COPY requirements.txt .

# 安装 requirements.txt 中列出的 Python 模块
RUN pip install -r requirements.txt

# 将 Dockerfile 所在目录下的所有文件复制到镜像中的 /app 目录下
COPY . .
EXPOSE 8989
CMD ["python", "app.py"]
