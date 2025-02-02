FROM python:3.10-slim
RUN apt-get update && apt-get install -y \
    git \
    libgomp1 \
    libdeflate-dev \
    && rm -rf /var/lib/apt/lists/*
RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/app/main.py"]
