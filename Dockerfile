FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AUTORAG_DB=/app/data/autorag.db
COPY pyproject.toml README.md ./
COPY autorag/ ./autorag/
RUN pip install --no-cache-dir . && useradd -m -u 10001 autorag && mkdir -p /app/data && chown -R autorag:autorag /app/data
USER autorag
EXPOSE 8000
CMD ["uvicorn", "autorag.api:app", "--host", "0.0.0.0", "--port", "8000"]
