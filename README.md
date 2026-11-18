# PersonalProfile

Plataforma para crear una página personal-profesional pública o privada en `/@nickname`.

Monorepo:

| Carpeta | Contenido |
|---|---|
| `frontend/` | Angular 22 + SSR (Node 24) |
| `backend/` | FastAPI (Python 3.13) |
| `docs/` | Contexto, arquitectura, roadmap, decisiones |
| `compose.yaml` | Entorno local: frontend + backend + PostgreSQL 18 |

## Requisitos

- Docker Engine con Docker Compose v2+ (en Windows: Docker en WSL2 o Docker Desktop).
- No hace falta Node ni Python en el host: todo se ejecuta en contenedores.
  Si quieres ejecutar herramientas fuera de Docker: Node `^22.22.3 || ^24.15` y Python 3.13.

## Arranque local

```bash
cp .env.example .env        # opcional: compose tiene valores por defecto de desarrollo
docker compose up --build --wait
```

| Servicio | URL |
|---|---|
| Frontend (SSR, `ng serve`) | http://localhost:4200 |
| API | http://localhost:8000/api/v1/health |
| Documentación OpenAPI (solo no-producción) | http://localhost:8000/api/docs |
| PostgreSQL | `localhost:5432` |

Los puertos se publican solo en `127.0.0.1`. El navegador llama a la API por rutas relativas `/api/...`;
el servidor de desarrollo de Angular las reenvía a `backend:8000` (`frontend/proxy.conf.json`).

Parar: `docker compose down` (añade `--volumes` para borrar los datos locales de PostgreSQL).

### Windows + WSL

Si el repositorio está en `C:\` y Docker corre en WSL, los cambios de archivos no generan eventos
inotify; por eso `ng serve` usa `--poll` y uvicorn `WATCHFILES_FORCE_POLLING`. Para más rendimiento,
clona el repositorio dentro del sistema de archivos de WSL (`~/...`).

## Comprobaciones

```bash
# Backend: lint + tests (incluye test de integración contra PostgreSQL)
docker compose exec -e RUN_DB_TESTS=1 backend sh -c "ruff check . && ruff format --check . && pytest"

# Frontend: lint + tests (Vitest) + build de producción con SSR
docker compose exec frontend sh -c "npx ng lint && npx ng test --watch=false && npx ng build --output-path /tmp/ng-dist"
```

El CI (`.github/workflows/ci.yml`) ejecuta lo mismo y además levanta Compose y comprueba la
conectividad frontend → backend → PostgreSQL.

## Variables de entorno

Ver `.env.example`. Nunca subas `.env` a Git. Variables relevantes:

| Variable | Servicio | Uso |
|---|---|---|
| `POSTGRES_USER/PASSWORD/DB` | db, backend | Credenciales locales |
| `DATABASE_URL` | backend | Construida por compose a partir de las anteriores |
| `CORS_ORIGINS` | backend | Orígenes permitidos, separados por comas |
| `ENVIRONMENT` | backend | `development`/`test`/`staging`/`production` (en `production` se desactiva `/api/docs`) |
| `NG_ALLOWED_HOSTS` | frontend | Hosts aceptados por el SSR de Angular (protección anti-SSRF) |

## Documentación

Empieza por [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
y [docs/ROADMAP.md](docs/ROADMAP.md).
