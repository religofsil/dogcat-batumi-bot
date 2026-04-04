# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend
WORKDIR /src
COPY miniapp/package.json miniapp/package-lock.json* ./miniapp/
WORKDIR /src/miniapp
RUN npm install
COPY miniapp/ .
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY --from=frontend /src/miniapp/dist /app/backend/app/static/miniapp
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/backend
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
