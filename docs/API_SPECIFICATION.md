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

## Convenciones (desde Fase 2)

- **Errores de negocio**: `{"error": {"code": "<código>", "message": "<texto para mostrar>"}}`.
- **Errores de validación**: `422` estándar de FastAPI: `{"detail": [{"loc": ["body", "<campo>"], "msg": "...", ...}]}`.
  El frontend asocia cada error a su campo mediante `loc`.
- **Sesión**: cookie HttpOnly `pp_session` (`__Host-pp_session` con HTTPS). Ver D-015.
- **CSRF**: las operaciones autenticadas que modifican datos exigen la cabecera `X-CSRF-Token` con el valor
  de la cookie legible `pp_csrf` (`__Host-pp_csrf` con HTTPS). Si falta o no coincide: `403 csrf_failed`.
- **Origin**: cualquier `POST/PUT/PATCH/DELETE` con cabecera `Origin` que no esté en `CORS_ORIGINS` recibe
  `403 origin_not_allowed`.
- **Rate limiting**: `429 rate_limited` con cabecera `Retry-After` (segundos).

| Código | HTTP | Cuándo |
|---|---|---|
| `not_authenticated` | 401 | Sin sesión, sesión caducada/revocada o cuenta inactiva |
| `invalid_credentials` | 401 | Login fallido (mensaje idéntico exista o no el email) |
| `csrf_failed` | 403 | Falta `X-CSRF-Token` o no coincide |
| `origin_not_allowed` | 403 | `Origin` no permitido en método que modifica datos |
| `email_taken` | 409 | Registro con email ya existente |
| `nickname_taken` | 409 | Registro con nickname ya existente |
| `rate_limited` | 429 | Límite superado |

## Auth (`/api/v1/auth`)

### `GET /nickname-availability?nickname=<valor>`
Informativo: **no reserva** el nickname. Normaliza (sin `@`, minúsculas). Límite: 60/min por IP.

`200` → `{"nickname": "ana-dev", "available": true, "reason": null}`
`reason`: `invalid` (formato) · `reserved` (ruta/término reservado) · `taken` (en uso).

### `POST /register`
Límite: 5/hora por IP. Crea usuario + perfil e **inicia sesión** (cookie de navegador).

```json
{
  "first_name": "Ana", "last_name": "García", "nickname": "@Ana-Dev",
  "birth_date": "1990-05-17", "location": "Sevilla", "job_title": "Desarrolladora",
  "email": "Ana@Example.com", "password": "…", "password_confirm": "…",
  "visibility": "public", "preferred_language": "es"
}
```

| Campo | Reglas |
|---|---|
| first_name, last_name | 1–100 caracteres (sin espacios extremos) |
| nickname | 3–30, `a-z 0-9 -`, sin guion al inicio/fin, no reservado; se guarda normalizado |
| birth_date | anterior a hoy; edad ≥ `MIN_REGISTRATION_AGE` (14) |
| location, job_title | 1–120 caracteres |
| email | email válido (sin dominios reservados), ≤ 254; se guarda en minúsculas |
| password | 7–30 caracteres (D-022); `password_confirm` debe coincidir |
| visibility | `public` (defecto) · `private` |
| preferred_language | `es` (defecto) · `en` |

Campos no listados (p. ej. `role`) → `422`. `display_name` se deriva de nombre + apellidos.

`201` → `MeResponse` + cookies · `409 email_taken | nickname_taken` · `422` · `429`

### `POST /login`
Límites: 20/15 min por IP y 10/15 min por email (cuentan también los intentos fallidos).

```json
{ "email": "ana@example.com", "password": "…", "remember_me": false }
```

`password`: 1–30 caracteres (contraseñas más largas → `422`).

- `remember_me: false` → cookie de navegador; el servidor caduca la sesión a las 12 h.
- `remember_me: true` → cookie persistente de 30 días (`Max-Age`).
- Invalida la sesión anterior de ese navegador (anti fijación de sesión) y actualiza `last_login_at`.

`200` → `MeResponse` + cookies · `401 invalid_credentials` · `422` · `429`

### `POST /logout`
Requiere sesión y `X-CSRF-Token`. Revoca la sesión en BD y borra las cookies.

`204` · `401 not_authenticated` · `403 csrf_failed`

### `GET /me`
`Cache-Control: private, no-store`.

`200` → `MeResponse` · `401 not_authenticated`

```json
{
  "id": "uuid", "email": "ana@example.com", "role": "user",
  "profile": {
    "nickname": "ana-dev", "display_name": "Ana García", "first_name": "Ana",
    "last_name": "García", "visibility": "public", "preferred_language": "es"
  }
}
```
Nunca incluye `birth_date` ni `password_hash`.
