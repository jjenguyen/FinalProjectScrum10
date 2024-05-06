# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

# syntax=docker/dockerfile:1
FROM python:3.12-slim as base

# Prevents Python from writing pyc files and keeps stdout and stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user 'appuser'
RUN adduser --disabled-password --gecos "" --home "/nonexistent" \
    --shell "/sbin/nologin" --uid 10001 appuser

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Change the ownership of the /app directory to appuser
COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]

