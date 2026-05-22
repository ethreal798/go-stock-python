# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci --prefer-offline || npm install

# 复制源码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段 - nginx 托管
FROM nginx:1.27-alpine AS production

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
