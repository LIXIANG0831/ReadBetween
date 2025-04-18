FROM docker.qdai.tech/python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY . /app

# 使用清华源安装依赖
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露端口
EXPOSE 8080

# 环境变量区分应用
ENV APP_ENV=prod

#设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone


# 启动应用
CMD ["sh", "-c", "celery -A readbetween.core.celery_app worker --loglevel=info & uvicorn readbetween.main:app --workers 2 --port 8080 --host 0.0.0.0"]
