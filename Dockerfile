# Stage 1 — Build: generate HTML from YAML
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/generate_home.py && \
    python scripts/generate.py data/ecosystem-macro.yaml web/macro.html && \
    python scripts/generate.py data/ecosystem.yaml web/ecosystem.html

# Stage 2 — Serve: nginx serves the web/ folder
FROM nginx:alpine
COPY --from=builder /app/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
