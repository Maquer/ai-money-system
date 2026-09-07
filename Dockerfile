FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 代码
COPY gateway.py .
COPY smart_router.py .
COPY subscription.py .
COPY referral_system.py .
COPY multi_crypto_monitor.py .
COPY crypto_monitor.py .
COPY marketing.py .
COPY dashboard.py .
COPY monitor.py .
COPY telegram_bot.py .
COPY discord_bot.py .

# 数据目录
RUN mkdir -p /app/money_data

# 环境变量
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# 启动（HF Spaces 用 7860 端口）
CMD ["python3", "gateway.py"]
