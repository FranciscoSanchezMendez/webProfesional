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

## Fase 1 — Backend base y modelo — COMPLETADA (2026-11-18)
- [x] Configuración Pydantic por entorno: `DATABASE_URL` como `SecretStr`, conversión a driver psycopg,
      validación de staging/producción (URL obligatoria, sin CORS `*`).
- [x] SQLAlchemy 2.1 síncrono (D-009) y Alembic 1.20 (`[tool.alembic]` en `pyproject.toml`). El health
      `ready` usa ya el engine de SQLAlchemy.
- [x] Modelos `User`/`Profile` con UNIQUE, FK en cascada y CHECK de normalización (D-010, D-011, D-012).
- [x] Migración inicial `f9b83d8d5ca7`, revisada manualmente.
- [x] Repositorio mínimo (`add_user_with_profile`, `get_user_by_email`, `get_profile_by_nickname`,
      `nickname_exists`).
- [x] Tests de repositorio, migración y configuración.
**Criterio:** DB creada y migraciones reproducibles. → Cumplido (local y CI: run `44405500209` sobre `bfd1ebb`, 3 jobs en verde, 37 tests).

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


## Fase 2 — Registro, login y sesión — COMPLETADA (2026-11-18)
- [x] Registro y validaciones (edad mínima 14, nicknames reservados, `extra="forbid"`) (D-014).
- [x] Hash Argon2id con normalización NFKC y rehash automático (D-018).
- [x] Nickname availability (`invalid` / `reserved` / `taken`).
- [x] Login/logout/me con «Recordarme» (D-015).
- [x] Sesión opaca en BD, cookies HttpOnly/SameSite/`__Host-`, CSRF por token + `Origin` (D-016).
- [x] Rate limiting en PostgreSQL (D-017).
- [x] Tests de auth, duplicados, validación, CSRF, caducidad y rate limiting.
**Criterio:** crear cuenta, iniciar sesión, cerrar sesión; duplicados rechazados. → Cumplido (local y CI: run `44412944104` sobre `5fdc3e3`, 3 jobs en verde).

### Pruebas ejecutadas (Fase 2)
| Comprobación | Resultado |
|---|---|
| `ruff check` / `ruff format --check` | OK |
| `pytest` completo contra PostgreSQL | 73 passed |
| Migración `8994bd5c2527` + roundtrip downgrade/upgrade + modelos == migraciones | OK |
| Registro: 201 + login automático; duplicados email/nickname (con distinta capitalización) → 409 | OK |
| Validación (10 casos: edad < 14, fecha futura, contraseña corta/distinta, nickname reservado/inválido, email, nombre vacío, `role` inyectado) → 422; edad exacta 14 → 201 | OK |
| Login: errores idénticos para contraseña mala, email inexistente y cuenta inactiva; sin cookies | OK |
| «Recordarme»: cookie sin `Max-Age` + 12 h en servidor / `Max-Age=2592000` | OK |
| Rotación de sesión en login; sesión caducada → 401; `/me` con `private, no-store` | OK |
| Logout sin/ con CSRF incorrecto → 403; correcto → 204 y sesión borrada | OK |
| `Origin` ajeno → 403; rate limit login/email, registro/IP, nickname/IP → 429 + `Retry-After` | OK |
| E2E con curl vía proxy del frontend (`localhost:4200/api`): flujo completo | OK |
| BD: hash `$argon2id$`, sesiones solo con hashes, claves de rate limit sin IP en claro; contraseña ausente de logs | OK |
| Imagen `prod` con Argon2 y configuración de producción | OK |

Pendiente para fases posteriores: tarea programada de limpieza de sesiones/contadores (Fase 10),
`FORWARDED_ALLOW_IPS` según el proxy de despliegue (Fase 10).

## Fase 3 — Angular base y autenticación — IMPLEMENTADA en local (2026-11-19), pendiente CI remoto
- [x] Shell, header (estado de sesión, menú de usuario), footer (enlaces, idioma, tema), 404 real en SSR.
- [x] Rutas `/login`, `/register` (guestGuard, `noindex`), `/about`, `/contact`, `/faq` (marcadores).
- [x] Formularios reactivos tipados con validación espejo de la API, errores bajo cada campo, nickname
      comprobado al perder el foco, errores 409/422 mapeados a su campo.
- [x] Estado de sesión con signals (D-019), `guestGuard`/`authGuard`, interceptores CSRF y 401,
      `returnUrl` sin redirecciones abiertas.
- [x] Traducciones ES/EN tipadas (D-020) y tema sistema/claro/oscuro sin parpadeo en SSR (D-021).
**Criterio:** flujos de registro/login utilizables en móvil y escritorio. → Cumplido en local.

### Pruebas ejecutadas (Fase 3)
| Comprobación | Resultado |
|---|---|
| `ng lint` (incluye reglas de accesibilidad de plantillas) | OK |
| `ng test` (Vitest): servicio de sesión, interceptores, guards, `safeReturnUrl`, validadores, páginas login/registro, header, footer | 39 passed |
| `ng build` (SSR) | OK |
| SSR con curl: idioma por cookie/`Accept-Language`, tema por cookie, títulos traducidos, `noindex` en login/registro/404, HTTP 404, cabecera sin datos de usuario | OK |
| Navegador real (Playwright 1.65, Chromium) a 390 px y 1280 px: 17 comprobaciones × 2 (registro completo, errores por campo, foco, nickname reservado/libre, contraseñas distintas, login fallido genérico, «Recordarme», guard, logout, idioma y tema persistentes, sin scroll horizontal, sin errores de consola) | 34/34 OK |
| Cabecera a 320 px y 390 px sin desbordamiento | OK (corregido: botones partidos en móvil) |
| Backend sin regresiones (`pytest`) | 73 passed |

Bug encontrado por los tests y corregido: los guards llamaban a `inject(Router)` después de un `await`
(fuera del contexto de inyección), lo que habría fallado al visitar `/login` con sesión.

No verificado: Firefox/Safari (solo Chromium); lectores de pantalla reales. La prueba de navegador fue
manual (script fuera del repo); automatizar E2E en CI queda como mejora.

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
