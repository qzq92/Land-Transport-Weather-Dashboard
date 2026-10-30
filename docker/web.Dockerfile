FROM node:22.20-alpine AS builder

ENV NODE_ENV=development \
    NPM_CONFIG_AUDIT=false \
    NPM_CONFIG_FUND=false

WORKDIR /app

COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then \
        npm ci; \
    else \
        npm install --package-lock=false; \
    fi

COPY frontend/ ./
RUN npm run build


FROM nginxinc/nginx-unprivileged:1.28-alpine AS runtime

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder --chown=101:101 /app/dist /usr/share/nginx/html

USER 101

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["wget", "-qO-", "http://127.0.0.1:8080/healthz"]
