FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "开始运行港股先行监控程序..."\n\
echo "交易时间: 09:15 - 10:30"\n\
echo "检查间隔: 600秒 (10分钟)"\n\
echo ""\n\
python main.py' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口（如果需要Web界面）
EXPOSE 8080

# 设置入口点
ENTRYPOINT ["/app/start.sh"]