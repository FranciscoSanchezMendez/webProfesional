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
- SQLAlchemy 2.x async o sync; elegir una estrategia y mantenerla.
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

## 7. Privacidad y caché

- Respuestas de perfiles privados: `Cache-Control: private, no-store`.
- Perfiles públicos pueden usar caché controlada, invalidada tras edición.
- No cachear respuestas autenticadas en CDN.
- SSR no debe usar datos de un usuario en caché compartida.
- No indexar privados ni borradores.
- API debe comprobar privacidad en cada acceso por nickname, post, comentario y media.

## 8. Entornos y ramas

Un único monorepo:
- `develop`: desarrollo local/integración.
- `staging`: entorno de preproducción.
- `main`: producción.

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
- SSR en edge puede requerir ajustes de compatibilidad Node/Web APIs.
- Almacenamiento de imágenes y tráfico pueden superar cuotas por uso de galerías.
- El correo transaccional será necesario para recuperación de contraseña futura; no se implementa ahora.
- SEO depende de contenido público útil, rendimiento y rastreo; no hay garantía de indexación.
