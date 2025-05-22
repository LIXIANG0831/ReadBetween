# 使用官方 Node.js 镜像作为构建环境
FROM docker.m.daocloud.io/library/nginx:alpine as builder

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json (或 yarn.lock)
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制环境变量
COPY .env ./

# 复制项目文件
COPY . .

# 构建生产环境的应用
RUN npm run build

# 使用 Nginx 作为生产服务器
FROM docker.m.daocloud.io/library/nginx:alpine

# 将构建好的文件从 builder 阶段复制到 Nginx 的默认静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置（如果有）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
