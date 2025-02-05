# 使用官方的 Nginx 镜像作为基础镜像
FROM docker.m.daocloud.io/library/nginx:alpine

# 将本地的前端资源目录复制到 Nginx 默认的静态文件目录
COPY dist /usr/share/nginx/html

# 替换 Nginx 默认的配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 Nginx 的默认端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
