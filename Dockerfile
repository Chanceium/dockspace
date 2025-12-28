# Multi-stage build: Build Vue frontend, then create Django container

# Stage 1: Build Vue.js frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy all frontend source files (postinstall needs these)
COPY frontend/ ./

# Install dependencies (postinstall script runs here, needs source files)
RUN npm ci --prefer-offline --no-audit

# Build for production (builds to /app/backend/dockspace/static/dist)
RUN npm run build

# Stage 2: Python/Django application
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Install pip and poetry
RUN pip install --no-cache-dir --upgrade pip poetry

# Install Python dependencies
COPY backend/pyproject.toml backend/poetry.lock ./backend/
WORKDIR /app/backend
RUN poetry install --no-root --no-ansi

# Copy Django application
WORKDIR /app
COPY backend/ ./backend/

# Copy built Vue frontend from stage 1
# Note: In the frontend-builder container, vite builds to /app/backend/dockspace/static/dist
COPY --from=frontend-builder /app/backend/dockspace/static/dist ./backend/dockspace/static/dist

EXPOSE 8000

WORKDIR /app/backend
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --config gunicorn.conf.py"]
