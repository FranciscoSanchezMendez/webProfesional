# Registro de decisiones

Formato: fecha · contexto · decisión · consecuencias.

## 2026-11-18 · Fase 0

### D-001 · Versiones base
- **Contexto:** versiones estables vigentes al iniciar el proyecto.
- **Decisión:** Angular 22.2 (Node 24.22.3), FastAPI 0.163 sobre Python 3.13.18, PostgreSQL 18.7. Imágenes
  Debian 13 `trixie-slim` (bookworm ya es oldstable y el IDE reportaba 15 CVE altas en `node:24-bookworm-slim`).
  Versiones fijadas en Dockerfiles, `requirements*.txt` y `package-lock.json`.
- **Consecuencias:** Angular 22 exige Node `^22.22.3 || ^24.15`. El Node del host (20.14) no es compatible,
  por lo que todo el tooling de frontend se ejecuta en contenedores. Python 3.13 en lugar de 3.14 por
  madurez del ecosistema; reevaluar en Fase 1.

### D-002 · Angular SSR con render por petición
- **Contexto:** los perfiles `/@nickname` son dinámicos y deben ser indexables.
- **Decisión:** proyecto creado con `--ssr`, `RenderMode.Server` para `**` (no prerender). Se usa el
  `server.ts` de Express generado por Angular.
- **Consecuencias:** el código debe ser SSR-safe desde el principio (sin `window`/`document` fuera de
  `afterNextRender`). La compatibilidad con Cloudflare Workers sigue pendiente (Fase 9); `AngularAppEngine`
  permite un handler fetch, pero no está probado.

### D-003 · Hosts permitidos del SSR por variable de entorno
- **Contexto:** Angular SSR rechaza (400) peticiones cuya cabecera `Host` no esté permitida (anti-SSRF).
  Con `security.allowedHosts: []` no se acepta ningún host.
- **Decisión:** no fijar dominios en `angular.json`; cada entorno define `NG_ALLOWED_HOSTS`.
- **Consecuencias:** staging/producción deben configurar sus dominios o el SSR fallará.

### D-004 · API en el mismo origen (`/api`)
- **Contexto:** la sesión usará cookies HttpOnly; el mismo origen simplifica cookies, SameSite y CORS.
- **Decisión:** el frontend usa rutas relativas `/api/v1/...`. En desarrollo, `ng serve` hace de proxy hacia
  `backend:8000`. CORS sigue configurado (`CORS_ORIGINS`) para acceso directo al puerto 8000.
- **Consecuencias:** en producción se necesita enrutar `/api` al backend (reverse proxy/edge) o decidir otra
  estrategia; pendiente para Fase 10. Las llamadas SSR → API (Fase 4) usarán una URL interna configurable.

### D-005 · Health: liveness y readiness separados
- **Decisión:** `/api/v1/health` (sin dependencias) y `/api/v1/health/ready` (comprueba PostgreSQL).
  En Fase 0 se usa `psycopg` directamente; en Fase 1 pasará a usar el engine de SQLAlchemy.
- **Consecuencias:** el healthcheck de producción usa liveness para no reiniciar la API si cae la BD.
  En Compose de desarrollo el backend usa readiness para que el frontend arranque con la BD lista.

### D-006 · Entorno Docker de desarrollo
- **Decisión:** Dockerfiles multi-stage (`dev`/`prod`), usuarios no-root (`appuser` uid 10001, `node`),
  puertos publicados solo en `127.0.0.1`, volumen `pgdata` montado en `/var/lib/postgresql` (cambio de
  PostgreSQL 18). Polling de ficheros activado para bind mounts desde Windows. `node_modules` y `.angular`
  como volúmenes anónimos propiedad de `node`.
- **Consecuencias:** funciona tanto en WSL sobre `C:` como en Linux nativo (verificado simulando un
  checkout propiedad de uid 1001).

### D-007 · Herramientas de calidad
- **Decisión:** backend con Ruff + pytest + `httpx2` (Starlette depreca `httpx` para `TestClient`);
  frontend con angular-eslint 22, Vitest (por defecto en Angular 22) y TypeScript `strict` + `strictTemplates`.

### D-008 · Nombres de ramas
- **Contexto:** la documentación inicial proponía `develop/staging/main`; el repositorio ya tenía
  `develop`, `main`, `preproduction` y `production`.
- **Decisión (usuario):** `develop` = desarrollo, `preproduction` = staging, `production` = producción.
  `main` se conserva sin uso hasta nueva decisión.
- **Consecuencias:** CI configurado para `develop`, `preproduction`, `production` y Pull Requests.
  Los entornos de staging/producción (Fase 10) se asociarán a `preproduction`/`production`.

## 2026-11-18 · Fase 1

### D-009 · SQLAlchemy síncrono
- **Contexto:** ARCHITECTURE.md pedía elegir sync o async y mantenerlo.
- **Decisión (usuario):** SQLAlchemy 2.x síncrono con psycopg 3. `get_engine()`/`get_sessionmaker()`
  perezosos, `get_db()` como dependencia (una sesión por petición), `expire_on_commit=False`.
- **Consecuencias:** endpoints `def` (threadpool de FastAPI). Suficiente para el objetivo de carga; si algún
  día hiciera falta async, psycopg 3 soporta ambos modos y el cambio quedaría acotado a `app/db` y repositorios.

### D-010 · Enumerados como VARCHAR + CHECK
- **Contexto:** los ENUM nativos de PostgreSQL requieren `ALTER TYPE` para añadir valores y complican
  los downgrades.
- **Decisión:** `sa.Enum(native_enum=False, create_constraint=True)` con valores `StrEnum` en Python.
- **Consecuencias:** añadir un valor = migración que recrea un `CHECK` con nombre conocido.

### D-011 · Integridad garantizada también en la base de datos
- **Decisión:** además de normalizar en la aplicación (`app/core/normalization.py`), la BD impone
  email en minúsculas sin espacios y formato de nickname mediante `CHECK`; UNIQUE en email, nickname y
  `profiles.user_id`. Migraciones automáticas solo en desarrollo; en entornos desplegados, paso explícito.
- **Consecuencias:** un error en la capa de aplicación no puede guardar datos duplicados por mayúsculas.
  Los errores de restricción llegarán como `IntegrityError` y la Fase 2 debe traducirlos a 409/422.

### D-012 · Desactivación de perfil y estado de cuenta
- **Contexto:** DATABASE.md dejaba abierto "is_suspended/deactivated".
- **Decisión:** `profiles.is_deactivated` (lo controla el usuario; perfil oculto, datos conservados) y
  `users.is_active` (bloqueo de cuenta por sistema/admin). Sin suspensión por moderación en el MVP.
- **Consecuencias:** las consultas públicas de perfil (Fase 4) deben filtrar `is_deactivated = false` y
  `users.is_active = true`.

### D-013 · Base de datos de test
- **Decisión:** tests de BD contra PostgreSQL real (no SQLite), en una base `*_test` indicada por
  `TEST_DATABASE_URL`. El fixture recrea el esquema `public`, aplica migraciones con Alembic y cada test
  corre en una transacción revertida. Se niega a ejecutarse si el nombre no termina en `_test`.
- **Consecuencias:** los tests validan las restricciones reales y la reproducibilidad de las migraciones.

## 2026-11-18 · Fase 2

### D-014 · Edad mínima de registro: 14 años
- **Contexto:** la fecha de nacimiento es obligatoria; la LOPDGDD fija 14 años para consentir sin autorización parental.
- **Decisión (usuario):** 14 años, configurable con `MIN_REGISTRATION_AGE`, validado en backend.
- **Consecuencias:** si la plataforma se dirige a otros países de la UE, revisar (RGPD art. 8: 16 por defecto).

### D-015 · Sesión opaca en BD con «Recordarme»
- **Decisión (usuario):** token aleatorio de 256 bits en cookie `HttpOnly`, `SameSite=Lax`, `Secure` y prefijo
  `__Host-` en staging/producción. En BD solo el SHA-256 (`sessions`). Sin «Recordarme»: cookie de navegador
  + caducidad en servidor a las 12 h. Con «Recordarme»: cookie y sesión de 30 días. Caducidad absoluta (sin
  renovación por uso). El login revoca la sesión previa del navegador (anti fijación). Registro = login automático
  con sesión de navegador.
- **Consecuencias:** logout y revocación inmediatos; cada petición autenticada consulta la BD (asumible).
  El SSR de perfiles privados (Fase 4) reenviará la cookie al backend sin cachear la respuesta.

### D-016 · CSRF: token sincronizado + Origin
- **Decisión:** token CSRF por sesión (hash en BD) entregado en cookie legible; las operaciones autenticadas que
  modifican datos exigen `X-CSRF-Token`. Además, middleware que rechaza métodos que modifican datos con un
  `Origin` fuera de `CORS_ORIGINS`. Login/registro (sin sesión) quedan protegidos por `SameSite=Lax` + `Origin`.
- **Consecuencias:** en cada entorno `CORS_ORIGINS` debe contener el origen público del frontend, aunque la API
  se sirva en el mismo origen. El frontend (Fase 3) añadirá la cabecera con un interceptor.

### D-017 · Rate limiting en PostgreSQL
- **Decisión (usuario):** contadores de ventana fija en `rate_limits` con `INSERT … ON CONFLICT`, commit inmediato
  (los intentos fallidos cuentan). Sujetos hasheados con SHA-256. Límites: login 20/15 min por IP y 10/15 min
  por email; registro 5/h por IP; nickname 60/min por IP.
- **Consecuencias:** funciona con varias instancias sin infraestructura extra. La IP depende de
  `--proxy-headers` y de configurar `FORWARDED_ALLOW_IPS` en el despliegue (Fase 10). Si la carga crece,
  `services/rate_limit.py` es el único punto a cambiar (Redis).

### D-018 · Contraseñas y errores de autenticación
- **Decisión:** Argon2id con `argon2-cffi` (parámetros RFC 9106 por defecto, rehash automático si cambian),
  normalización Unicode NFKC, longitud 12–128 sin reglas de composición (criterio NIST SP 800-63B).
  **Longitud sustituida por D-022 (7–30).**
  Login con mensaje genérico y verificación Argon2 también cuando el email no existe (mismo tiempo).
  El registro sí informa de `email_taken`/`nickname_taken` (409) por usabilidad; mitigado por rate limiting.
- **Consecuencias:** la enumeración de emails vía registro es posible a baja velocidad; reevaluar si hay abuso.

## 2026-11-19 · Fase 3

### D-019 · Sesión resuelta en el navegador; el HTML SSR no depende del usuario
- **Contexto:** el SSR no reenvía la cookie de sesión al backend y el HTML de páginas públicas podría
  acabar en cachés compartidas.
- **Decisión:** `AuthService.ensureLoaded()` consulta `/me` solo en el navegador. En SSR el estado es
  `unknown` y la cabecera reserva el hueco sin botones. `guestGuard` espera a `/me`; `authGuard` deja pasar en
  SSR (las rutas protegidas futuras usarán `RenderMode.Client` y la API autoriza siempre).
- **Consecuencias:** ningún dato de usuario en el HTML del servidor. En Fase 4 los perfiles privados
  necesitarán una estrategia propia (reenvío de cookie con `Cache-Control: private, no-store`).

### D-020 · Traducciones con ngx-translate y diccionarios TypeScript empaquetados
- **Contexto:** el idioma se elige y recuerda en caliente; el i18n nativo de Angular compila un build por idioma.
- **Decisión:** `@ngx-translate/core` 18 con un loader que importa `es.ts`/`en.ts` (import dinámico, sin
  HTTP: funciona igual en SSR). `en.ts` está tipado con las claves de `es.ts`, así que falta de claves = error
  de compilación. Preferencia en cookie `pp_lang`, leída también en SSR (`REQUEST`).
- **Consecuencias:** el HTML depende de cookies (`pp_lang`, `pp_theme`): no debe cachearse en CDN sin
  variar por ellas (a considerar en Fase 9).

### D-021 · Diseño provisional por tokens
- **Contexto:** `UI_UX_SPECIFICATION.md` estaba vacío y la referencia visual no está en el repositorio.
- **Decisión:** diseño minimalista neutro con tokens CSS, temas claro/oscuro/sistema (cookie `pp_theme`).
- **Consecuencias:** al recibir la referencia, se ajustan los tokens y se completa la especificación.

## 2026-11-20

### D-022 · Longitud de contraseña 7–30 (decisión del usuario)
- **Contexto:** D-018 fijaba 12–128 caracteres.
- **Decisión (usuario):** `PASSWORD_MIN_LENGTH = 7`, `PASSWORD_MAX_LENGTH = 30` en
  `backend/app/schemas/auth.py`; el frontend replica los mismos valores en `features/auth/validators.ts`.
  El máximo también se aplica al campo `password` del login.
- **Consecuencias:** por debajo de la recomendación de NIST SP 800-63B (mínimo 8, y aceptar al menos 64
  caracteres). Un máximo de 30 puede rechazar contraseñas generadas por gestores de contraseñas. El límite
  de coste de Argon2 no requiere un máximo tan bajo. Mitigaciones existentes: Argon2id y rate limiting.
  Las cuentas ya creadas con contraseñas de más de 30 caracteres no podrán iniciar sesión.
