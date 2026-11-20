# Arquitectura técnica

## 1. Principios

- Monolito modular FastAPI, no microservicios.
- Angular como SPA con SSR/hidratación para rutas públicas indexables.
- PostgreSQL como única base relacional.
- Object storage S3-compatible para imágenes en producción.
- Docker Compose para desarrollo local.
- Configuración por variables de entorno.
- Infraestructura intercambiable: no acoplar lógica de negocio al proveedor cloud.

## 2. Stack propuesto

### Backend
- Python: versión estable soportada por dependencias al iniciar proyecto.
- FastAPI.
- Pydantic v2.
- SQLAlchemy 2.x **síncrono** con psycopg 3 (D-009): `Session` por petición vía `get_db`, endpoints `def`
  ejecutados en el threadpool de FastAPI.
- Alembic.
- PostgreSQL.
- Argon2id para hash de contraseñas.
- pytest + httpx.
- Ruff para lint/format.
- Rate limiting con solución mantenida compatible con despliegue stateless.

### Frontend
- Angular versión estable vigente al inicio.
- TypeScript strict.
- Angular Router.
- Reactive Forms.
- Angular SSR/hydration para SEO.
- Librería de iconos mantenida; iconos de marca mediante SVG oficiales/licencia apropiada, sin copiar logos incorrectos.
- Traducciones español/inglés mediante mecanismo mantenido.

### Infraestructura
- Docker y Docker Compose.
- GitHub Actions para lint, tests y build.
- Cloudflare Pages/Workers para frontend si el flujo Angular SSR es compatible con los requisitos.
- Google Cloud Run para FastAPI como alternativa de backend con escala a cero.
- Neon Postgres como opción inicial de base de datos.
- Cloudflare R2 para imágenes.

### Versiones fijadas (Fase 0, 2026-11-18)

| Componente | Versión | Nota |
|---|---|---|
| Node (contenedor) | 24.22.3 `trixie-slim` | Angular 22 exige `^22.22.3 \|\| ^24.15` |
| Angular / CLI / SSR | 22.2.x | `RenderMode.Server`, Vitest, angular-eslint 22.7 |
| Python (contenedor) | 3.13.18 `slim-trixie` | |
| FastAPI / uvicorn | 0.163.2 / 0.54.0 | |
| pydantic-settings | 2.16.3 | |
| psycopg | 3.3.9 | driver de SQLAlchemy (`postgresql+psycopg://`) |
| SQLAlchemy / Alembic | 2.1.9 / 1.20.1 | síncrono (D-009); Alembic configurado en `pyproject.toml` |
| argon2-cffi / email-validator | 25.1.0 / 2.4.0 | hash de contraseñas (D-018) / `EmailStr` |
| @ngx-translate/core | 18.1.0 | traducciones ES/EN en caliente (D-020) |

### Frontend implementado (Fase 3)

```text
frontend/src/app/
├── core/
│   ├── auth/      AuthService (signals: unknown/anonymous/authenticated), guards, interceptores CSRF y 401
│   ├── http/      CookieStore (navegador + SSR vía REQUEST), parseApiError
│   ├── i18n/      es.ts / en.ts tipados, LanguageService, SeoTitleStrategy (title + robots)
│   └── theme/     ThemeService (sistema/claro/oscuro en cookie)
├── shared/        header, footer, field-error, forms
└── features/      home, auth (login, register, validators), info, not-found
```

- Zoneless (por defecto en Angular 22) + signals; componentes standalone; formularios reactivos tipados.
- Idioma y tema se aplican en `provideAppInitializer` (también en SSR) leyendo cookies: sin parpadeo.
- La sesión se resuelve solo en el navegador (D-019); el HTML del SSR nunca contiene datos de usuario.
- Rutas desconocidas → 404 real en SSR (`app.routes.server.ts`).
| PostgreSQL | 18.7-alpine | volumen en `/var/lib/postgresql` (cambio de la imagen 18+) |

Motivos y consecuencias en `docs/DECISIONS.md` (D-001 a D-007).

### Entorno local (implementado)

```text
Navegador ──► :4200 frontend (ng serve + SSR) ──/api proxy──► backend:8000 (FastAPI) ──► db:5432 (PostgreSQL)
                                               (red interna de Compose)
```

- El frontend llama a la API con rutas relativas `/api/v1/...` (mismo origen); ver D-004.
- `GET /api/v1/health` (liveness) y `GET /api/v1/health/ready` (readiness con PostgreSQL); ver D-005.
- SSR: hosts permitidos por `NG_ALLOWED_HOSTS` en cada entorno; ver D-003.
- Migraciones: automáticas al arrancar solo en desarrollo; en staging/producción, paso explícito con la
  imagen `prod` (`alembic upgrade head`) antes de desplegar la nueva versión (D-011).

## 3. Arquitectura lógica

```text
Browser / crawler
      |
      v
Angular SSR / static assets
      |
      | HTTPS REST
      v
FastAPI (modular monolith)
      |
      +---- Auth module
      +---- Users / Profiles module
      +---- Links module
      +---- Posts module
      +---- Comments module
      +---- Likes module
      +---- Admin module
      +---- Media module
      |
      +---- PostgreSQL
      |
      +---- S3-compatible object storage (R2)
```

Angular SSR debe consultar el backend en servidor con credenciales técnicas limitadas o endpoints públicos seguros. No debe filtrar cookies ni datos de otros usuarios. Para perfil privado, el SSR debe verificar sesión y permiso antes de recuperar/renderizar el contenido.

## 4. Organización backend sugerida

```text
backend/
├── app/
│   ├── main.py
│   ├── core/              # config, security, dependencies
│   ├── db/                # session, base, migrations integration
│   ├── models/
│   ├── schemas/
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── profiles.py
│   │   ├── links.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   ├── likes.py
│   │   └── admin.py
│   ├── services/
│   ├── repositories/
│   └── storage/
├── tests/
├── alembic/
├── Dockerfile
└── pyproject.toml
```

No crear capas vacías por obligación: introducir services/repositories donde aporten separación útil.

## 5. Organización frontend sugerida

```text
frontend/
├── src/
│   ├── app/
│   │   ├── core/          # auth, guards, interceptors, config
│   │   ├── shared/        # header, footer, buttons, dialogs
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── profile/
│   │   │   ├── posts/
│   │   │   ├── comments/
│   │   │   └── admin/
│   │   └── app.routes.ts
│   ├── assets/i18n/
│   └── styles/
├── Dockerfile
└── package.json
```

## 6. Seguridad de sesión

Evaluar e implementar una estrategia coherente:
- Cookie HttpOnly, Secure en producción, SameSite=Lax o Strict según flujos.
- Token de acceso corto y refresh controlado o sesión opaca almacenada en DB.
- Si se autentica mediante cookies, implementar CSRF apropiado para operaciones mutables.
- No guardar tokens de larga duración en localStorage.
- Rotación/invalidez de refresh o sesiones.
- Cookies y dominios configurados por entorno.

Claude debe documentar la estrategia final antes de implementarla.

**Estrategia implementada (Fase 2):** sesión opaca en PostgreSQL (D-015), CSRF por token sincronizado +
comprobación de `Origin` (D-016), rate limiting en PostgreSQL (D-017) y Argon2id (D-018). Contratos en
`docs/API_SPECIFICATION.md`. Código: `app/api/deps.py` (sesión/CSRF/cookies), `app/services/auth.py`,
`app/services/rate_limit.py`, `app/core/security.py`.

## 7. Privacidad y caché

- Respuestas de perfiles privados: `Cache-Control: private, no-store`.
- Perfiles públicos pueden usar caché controlada, invalidada tras edición.
- No cachear respuestas autenticadas en CDN.
- SSR no debe usar datos de un usuario en caché compartida.
- No indexar privados ni borradores.
- API debe comprobar privacidad en cada acceso por nickname, post, comentario y media.

## 8. Entornos y ramas

Un único monorepo (D-008):
- `develop`: desarrollo local/integración.
- `preproduction`: entorno de preproducción (staging).
- `production`: producción.
- `main`: sin uso por ahora.

Flujo previsto: `develop` → PR → `preproduction` → PR → `production`. El CI se ejecuta en push a
esas tres ramas y en cada Pull Request.

Cada entorno debe tener:
- Variables y secretos independientes.
- Base de datos independiente (staging puede usar una base pequeña separada).
- Bucket o prefijo de almacenamiento independiente.
- CORS/orígenes permitidos propios.
- Migraciones controladas.

No asumir que tres ramas implican tres despliegues gratuitos sin coste. En el MVP, local + preview y un staging ligero pueden ser suficientes; producción se activa al final.

## 9. Despliegue de bajo coste recomendado

Opción inicial a validar con límites vigentes:
- Angular: Cloudflare Workers/Pages. Confirmar el soporte concreto del builder SSR elegido; no desplegar como SPA pura si eso impide indexar perfiles dinámicos.
- FastAPI: Google Cloud Run con min instances = 0, request-based billing, límite de instancias y alertas de presupuesto. Revisar región y cuota gratuita.
- PostgreSQL: Neon Free (1 GB, cuotas mensuales de compute y transferencia según plan vigente).
- Imágenes: Cloudflare R2 (10 GB-month de almacenamiento estándar gratuito y cuotas de operaciones publicadas).
- Dominio: subdominio del proveedor durante desarrollo; dominio propio cuando se lance, con coste anual aparte.

Alternativa simplificada: Supabase Free ofrece PostgreSQL, pero el proyecto puede pausarse tras una semana de inactividad y tiene límites de almacenamiento/egress; no depender de su Auth si el requisito es aprender y controlar FastAPI.

Render Free no se recomienda como backend/base de datos de producción persistente: el servicio duerme por inactividad, filesystem efímero y su Postgres gratuito expira a los 30 días según su documentación actual.

## 10. Backups y recuperación

Antes de producción:
- Definir política de backups de PostgreSQL.
- Automatizar `pg_dump` cifrado y almacenar copia fuera de la base principal.
- Probar restauración en staging.
- No asumir que el free tier incluye backups automáticos.
- Documentar RPO/RTO realistas.
- No guardar secretos de backup en GitHub ni en el propio bucket sin cifrado.

## 11. Riesgos conocidos

- Free tiers pueden cambiar o suspender servicios.
- SSR en edge puede requerir ajustes de compatibilidad Node/Web APIs. El proyecto usa hoy el `server.ts`
  de Express (Node); para Cloudflare Workers habría que exponer un handler fetch con `AngularAppEngine`
  y validar las dependencias. Si no encaja, alternativa: frontend SSR en Cloud Run junto al backend.
- Enrutado de `/api` en producción: el proxy de `ng serve` solo existe en desarrollo (D-004).
- Las llamadas SSR → API (Fase 4) no deben reenviar cookies de usuario a cachés compartidas ni usar la
  URL pública si existe una interna.
- Almacenamiento de imágenes y tráfico pueden superar cuotas por uso de galerías.
- El correo transaccional será necesario para recuperación de contraseña futura; no se implementa ahora.
- SEO depende de contenido público útil, rendimiento y rastreo; no hay garantía de indexación.
