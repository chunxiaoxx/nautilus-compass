# 多阶段构建 - 优化镜像大小
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-minimal.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements-minimal.txt

# 最终镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 nautilus

# 从builder复制Python包到nautilus用户目录
COPY --from=builder --chown=nautilus:nautilus /root/.local /home/nautilus/.local

# 确保Python包在PATH中
ENV PATH=/home/nautilus/.local/bin:$PATH

# 复制应用代码
COPY --chown=nautilus:nautilus . .

USER nautilus

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()"

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
