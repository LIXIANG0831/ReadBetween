FROM m.daocloud.io/docker.io/library/python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY . /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    patch \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 使用清华源安装依赖
RUN cd /app/readbetween && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露端口
EXPOSE 8080

#设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 设置Python路径
ENV PYTHONPATH=/app/readbetween

# 启动应用
CMD ["sh", "-c", "celery -A readbetween.core.celery_app worker --loglevel=info & uvicorn readbetween.main:app --workers 2 --port 8080 --host 0.0.0.0"]
