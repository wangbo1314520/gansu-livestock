# -*- coding: utf-8 -*-
# 后端镜像（部署预演，未实际 build）
# 说明：项目 venv 用 Python 3.14；若构建时 python:3.14-slim 标签不可用，改用 python:3.12-slim
# 并在 docs/部署指南.md 记录版本差异（依赖均兼容 3.12+）。
FROM python:3.14-slim

WORKDIR /app

# 系统依赖（lxml 轮子若缺需 gcc；slim 一般有预编译轮可省）
ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 项目结构：backend 为工作目录，spider/predict 为同级依赖包
COPY backend/ ./backend/
COPY spider/ ./spider/
COPY predict/ ./predict/
COPY scripts/ ./scripts/

WORKDIR /app/backend
EXPOSE 5000

# 环境变量：DB_PASSWORD 必填；APP_MODE 默认 school（home 为家用版）
ENV APP_MODE=school
CMD ["python", "app.py"]
