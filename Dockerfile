# 使用包含 Python 3 的官方 Ubuntu 镜像作为基础镜像
FROM python:3.8

# 安装所需 Python 包
RUN pip install requests feedparser pytz selenium selenium-stealth aiohttp beautifulsoup4 tqdm

# 将本地的 main.py 文件复制到容器中
COPY main.py /app/main.py

# 设置工作目录
WORKDIR /app

# 执行 Python 脚本 main.py
CMD ["python", "main.py"]
