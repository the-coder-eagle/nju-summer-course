FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip install --no-cache-dir uvicorn
COPY src ./src
COPY arena ./arena
COPY web ./web
COPY tests ./tests
ENV PYTHONPATH=/app/src:/app
EXPOSE 8000
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
