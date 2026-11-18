# syntax=docker/dockerfile:1
FROM node:24.22.3-trixie-slim AS deps
ENV NG_CLI_ANALYTICS=false
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

# --- Desarrollo: ng serve con proxy /api -> backend y polling (bind mount desde Windows/WSL)
FROM deps AS dev
COPY --chown=node:node . .
# Directorio de caché propiedad de node (se monta como volumen anónimo en compose).
RUN mkdir -p .angular
EXPOSE 4200
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--proxy-config", "proxy.conf.json", "--poll", "1000"]

# --- Build de producción (navegador + servidor SSR)
FROM deps AS build
COPY --chown=node:node . .
RUN npm run build

# --- Producción: servidor Node SSR (Express ya va empaquetado en server.mjs)
FROM node:24.22.3-trixie-slim AS prod
ENV NODE_ENV=production PORT=4000
WORKDIR /app
COPY --from=build --chown=node:node /app/dist/personal-profile ./dist
USER node
EXPOSE 4000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["node", "-e", "fetch('http://localhost:4000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
CMD ["node", "dist/server/server.mjs"]
