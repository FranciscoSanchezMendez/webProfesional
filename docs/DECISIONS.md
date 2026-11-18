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
