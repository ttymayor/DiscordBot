FROM python:3.13.2-slim

WORKDIR /app

# 安裝 ffmpeg（必須的）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ps aux | grep "python bot.py" | grep -v grep || exit 1

CMD ["python", "bot.py"]
