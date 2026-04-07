# commented due to docker error on scaler server
#FROM python:3.10-slim
FROM ghcr.io/astral-sh/uv:python3.10-bookworm

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "7860"]