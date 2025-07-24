FROM python:3.10-slim-buster

WORKDIR /app

COPY pyproject.toml ./

RUN pip install uv
RUN uv pip install --system .

COPY . /app

EXPOSE 8000

CMD ["bash", "-c", "python create_db_tables.py && PYTHONPATH=/app uvicorn backend.server:app --host 0.0.0.0 --port 8000"] 