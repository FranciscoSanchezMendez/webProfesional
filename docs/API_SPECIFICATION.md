# Especificación de la API

Base: `/api/v1`. JSON. En desarrollo, el frontend accede por el mismo origen (`/api/...` vía proxy).
OpenAPI interactivo en `/api/docs` (desactivado con `ENVIRONMENT=production`).

## Health

### `GET /api/v1/health` — liveness
El proceso responde. No consulta dependencias externas. Uso: healthcheck de contenedor/plataforma.

`200 OK`
```json
{ "status": "ok" }
```

### `GET /api/v1/health/ready` — readiness
La API puede atender peticiones: PostgreSQL responde a `SELECT 1` (timeout de conexión 3 s).

`200 OK`
```json
{ "status": "ok", "database": "ok" }
```

`503 Service Unavailable`
```json
{ "status": "error", "database": "unavailable" }
```

No expone detalles del error (host, usuario, mensaje del driver).
