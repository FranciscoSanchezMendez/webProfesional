# Roadmap de implementación

Estados iniciales: TODO. Claude debe actualizar este archivo después de cada hito.

## Fase 0 — Repositorio y entorno — COMPLETADA (2026-11-18)
- [x] Monorepo `frontend/` + `backend/` + `docs/`.
- [x] Ramas: `develop` (desarrollo), `preproduction` (staging), `production` (producción); `main` sin uso
      (D-008). En el remoto existen `develop` y `production`; `preproduction` aún es solo local.
- [x] Commit de Fase 0 en `develop` (`b394db4`) y push a `origin/develop` (realizado por el usuario).
- [x] `.gitignore` (raíz, frontend, backend), `.env.example`, `README.md`.
- [x] Docker Compose (`compose.yaml`): Angular 22 SSR, FastAPI, PostgreSQL 18; Dockerfiles multi-stage dev/prod.
- [x] Healthchecks en los tres servicios y conexión frontend → backend → PostgreSQL.
- [x] CI inicial (`.github/workflows/ci.yml`): lint/tests/build + Compose. Run `44298608018` sobre `develop`
      (`b394db4`): jobs `backend`, `frontend` y `docker` en verde (4m47s); test de integración con PostgreSQL
      ejecutado. Runner fijado después a `ubuntu-24.04` (aviso de migración de `ubuntu-latest` a Ubuntu 26).
**Criterio de salida:** levantar el entorno local con un comando y ejecutar checks verdes. → Cumplido (local y CI).

### Pruebas ejecutadas (Fase 0)
Entorno: Windows 11 + Docker Engine 29.9.1 / Compose v5.6.0 en WSL2 (Ubuntu).

| Comprobación | Resultado |
|---|---|
| `docker compose up --build --wait` | db, backend, frontend `healthy` |
| Backend `ruff check` / `ruff format --check` | OK |
| Backend `pytest` (3 unitarios + 1 integración con PostgreSQL) | 4 passed |
| Frontend `ng lint` | OK |
| Frontend `ng test` (Vitest) | 3 passed |
| Frontend `ng build` (SSR) | OK |
| Windows → `localhost:8000/api/v1/health` | `{"status":"ok"}` |
| Windows → `localhost:4200/api/v1/health/ready` (proxy → backend → db) | `{"status":"ok","database":"ok"}` |
| Contenedor frontend → `backend:8000` (red interna) | OK |
| HTML de `/` renderizado en servidor (SSR) | contiene `<h1>PersonalProfile</h1>` |
| BD parada → readiness | `503 {"status":"error","database":"unavailable"}`; recupera al reiniciar |
| Imágenes `prod` backend/frontend | arrancan `healthy`, usuarios no-root, `/api/docs` 404 en producción |
| Recarga en caliente (uvicorn y ng serve) sobre `C:` vía WSL | OK con polling |
| `ng serve` con código propiedad de otro uid (simula Linux nativo / CI) | OK |

No verificado: render de la página en un navegador real
(se verificó el HTML SSR y la ruta `/api` que usa el navegador, no la hidratación visual).

## Fase 1 — Backend base y modelo — IMPLEMENTADA en local (2026-11-18), pendiente CI remoto
- [x] Configuración Pydantic por entorno: `DATABASE_URL` como `SecretStr`, conversión a driver psycopg,
      validación de staging/producción (URL obligatoria, sin CORS `*`).
- [x] SQLAlchemy 2.1 síncrono (D-009) y Alembic 1.20 (`[tool.alembic]` en `pyproject.toml`). El health
      `ready` usa ya el engine de SQLAlchemy.
- [x] Modelos `User`/`Profile` con UNIQUE, FK en cascada y CHECK de normalización (D-010, D-011, D-012).
- [x] Migración inicial `f9b83d8d5ca7`, revisada manualmente.
- [x] Repositorio mínimo (`add_user_with_profile`, `get_user_by_email`, `get_profile_by_nickname`,
      `nickname_exists`).
- [x] Tests de repositorio, migración y configuración.
**Criterio:** DB creada y migraciones reproducibles. → Cumplido en local.

### Pruebas ejecutadas (Fase 1)
| Comprobación | Resultado |
|---|---|
| `ruff check` / `ruff format --check` | OK |
| `pytest` (health, config, migraciones, repositorio) contra `personalprofile_test` | 37 passed |
| Migraciones: `downgrade base` → `upgrade head` y modelos == migraciones (`compare_metadata`) | OK |
| Restricciones reales: email/nickname duplicados (con distinta capitalización), 2.º perfil por usuario, email no normalizado, 7 nicknames inválidos, >30 caracteres, rol desconocido, cascada al borrar usuario | rechazados como se espera |
| Backend en Compose aplica `alembic upgrade head` al arrancar | `f9b83d8d5ca7 (head)` |
| Restricciones en `pg_constraint` de la base de desarrollo | PK, FK, UQ y CK con nombres deterministas |
| Aislamiento: los tests no modifican la base de desarrollo | OK |
| Imagen `prod` ejecuta `alembic current` contra la BD | OK |
| `alembic upgrade head --sql` (modo offline) | genera el DDL |
| Health `ready` vía proxy del frontend | `{"status":"ok","database":"ok"}` |

No verificado aún: ejecución del CI en GitHub con estos cambios.

## Fase 2 — Registro, login y sesión
- [ ] Registro y validaciones.
- [ ] Hash Argon2id.
- [ ] Nickname availability.
- [ ] Login/logout/me.
- [ ] Sesión segura y CORS/CSRF.
- [ ] Tests de auth, duplicados y rate limiting.
**Criterio:** crear cuenta, iniciar sesión, cerrar sesión; duplicados rechazados.

## Fase 3 — Angular base y autenticación
- [ ] Shell, header, footer.
- [ ] Rutas login/registro.
- [ ] Formularios reactivos.
- [ ] Estado de sesión, guards e interceptor.
- [ ] Traducciones ES/EN y tema claro/oscuro.
**Criterio:** flujos de registro/login utilizables en móvil y escritorio.

## Fase 4 — Perfil público/privado
- [ ] Perfil `/@nickname`.
- [ ] Home `/` del creador.
- [ ] Edición de datos.
- [ ] Privacidad pública/privada.
- [ ] Avatar y cover.
- [ ] Autorización backend y pruebas de filtrado.
**Criterio:** perfil público visible anónimamente; privado solo para usuarios autenticados; no hay filtración en SSR/API.

## Fase 5 — Enlaces
- [ ] CRUD de enlaces.
- [ ] Detección de plataforma.
- [ ] Iconos y orden.
- [ ] Validación de URL.
**Criterio:** enlaces se gestionan y renderizan correctamente.

## Fase 6 — Posts e imágenes
- [ ] CRUD posts, borradores y publicación.
- [ ] Portada + imágenes secundarias.
- [ ] Storage abstraction local/S3.
- [ ] Carrusel y vista detalle.
- [ ] Enlaces externos del post.
- [ ] Destacar/fijar.
**Criterio:** propietario publica proyecto completo y visitante autorizado lo consulta.

## Fase 7 — Comentarios y likes
- [ ] Comentarios registrados/anónimos.
- [ ] Respuestas en hilo.
- [ ] Eliminar comentarios como propietario.
- [ ] Desactivar comentarios por post.
- [ ] Likes/unlikes autenticados.
- [ ] Rate limits y protección anti-spam.
**Criterio:** pruebas de permisos, duplicados, spam básico y privacidad.

## Fase 8 — Admin
- [ ] Crear usuario inicial normal.
- [ ] Documentar SQL para elevar manualmente rol en PostgreSQL.
- [ ] Listado paginado de usuarios.
- [ ] Protección por rol y tests.
**Criterio:** admin accede; usuario normal recibe 403.

## Fase 9 — SEO, rendimiento y legal
- [ ] Angular SSR/hydration probado en hosting destino.
- [ ] Metadatos dinámicos, canonical, Open Graph.
- [ ] Sitemap y robots.
- [ ] Schema.org adecuado.
- [ ] Optimización de imágenes y Core Web Vitals.
- [ ] Páginas legales RGPD/cookies/condiciones preparadas y revisadas.
**Criterio:** HTML público contiene contenido indexable; privados/borradores no aparecen.

## Fase 10 — Despliegue y operación
- [ ] Staging y producción separados.
- [ ] Secretos y variables por entorno.
- [ ] Storage remoto.
- [ ] Backups automáticos y prueba de restauración.
- [ ] Alertas de coste/cuota.
- [ ] Dominio propio y HTTPS.
- [ ] Monitorización básica.
**Criterio:** despliegue reproducible, rollback y restauración documentados.

## Fuera del MVP / futuras versiones
- [ ] Recuperación de contraseña.
- [ ] Verificación de email.
- [ ] Google OAuth.
- [ ] Denuncias/moderación.
- [ ] Planes premium y pagos.
- [ ] Publicidad.
- [ ] Analítica avanzada.
