# Stage 1: Build Next.js frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + static frontend
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend, services, database, configs
COPY backend/ ./backend/
COPY services/ ./services/
COPY database/ ./database/
COPY config/ ./config/ 2>/dev/null || true
COPY prompts.yml rules.yml constants.py ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY --from=frontend-build /app/frontend/public ./frontend/public
COPY --from=frontend-build /app/frontend/package.json ./frontend/
COPY --from=frontend-build /app/frontend/node_modules ./frontend/node_modules

# Install Node.js for Next.js server
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy startup script
COPY <<'EOF' /app/start.sh
#!/bin/sh
cd /app/frontend && node_modules/.bin/next start -p 3000 &
cd /app && uvicorn backend.main:app --host 0.0.0.0 --port 8000
EOF
RUN chmod +x /app/start.sh

EXPOSE 3000 8000

CMD ["/app/start.sh"]
