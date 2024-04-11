# 使用官方 Ubuntu 镜像作为基础镜像
FROM ubuntu

# 更新包管理器并安装 Python 3.8 和相关依赖
RUN apt-get update && apt-get install -y python3.8 python3-pip

# 安装所需 Python 包
RUN pip3 install requests feedparser pytz selenium selenium-stealth aiohttp beautifulsoup4 tqdm

# 将本地的 main.py 文件复制到容器中
COPY main.py /app/main.py

# 设置工作目录
WORKDIR /app

# 执行 Python 脚本 main.py
CMD ["python3", "main.py"]
