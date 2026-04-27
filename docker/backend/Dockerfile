FROM python:3.11-slim

WORKDIR /app

COPY pfe-backend/pyproject.toml /app/pyproject.toml
COPY pfe-backend/poetry.lock /app/poetry.lock
RUN pip install --no-cache-dir poetry poetry-plugin-export && \
    poetry export -f requirements.txt --without-hashes -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

COPY pfe-backend /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
