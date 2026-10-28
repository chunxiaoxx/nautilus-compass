# ── 基础镜像：按任务语言选择 ──
# Go:     mirror.aone.alibaba-inc.com/mirrors/golang:1.22-bookworm
# Python: mirror.aone.alibaba-inc.com/mirrors/python:3.12-bookworm
# Java:   mirror.aone.alibaba-inc.com/mirrors/openjdk:17-bookworm
FROM mirror.aone.alibaba-inc.com/mirrors/golang:1.22-bookworm

# 替换 apt 源 + 安装必要工具（patch 为 solve.sh 必需）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    curl procps git patch \
    && rm -rf /var/lib/apt/lists/*

# ── 语言相关环境变量（按需保留） ──
# Go
ENV GOPROXY=https://goproxy.cn,direct
ENV GOFLAGS="-mod=mod"

# Python
# ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /workspace

COPY workspace/ /workspace/
