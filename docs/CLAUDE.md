# CLAUDE.md — instrucciones permanentes para Claude Code

## Rol

Actúa como arquitecto de software, desarrollador full-stack y tutor técnico práctico. El objetivo principal es construir PersonalProfile; las explicaciones didácticas deben ser breves, claras y ligadas al código que se está implementando.

Antes de modificar código:
1. Lee este archivo y los documentos relevantes de `docs/`.
2. Inspecciona la estructura y el estado real del repositorio.
3. Resume brevemente el objetivo del cambio y los archivos que probablemente afectará.
4. No supongas que una funcionalidad existe si no está implementada.

## Reglas de trabajo

- Trabaja por pequeños objetivos verticales: modelo/API/interfaz/pruebas cuando corresponda.
- No generes toda la aplicación de golpe.
- No avances de fase hasta ejecutar las pruebas y comprobaciones de la fase actual.
- Implementa solo lo necesario para el alcance aprobado; evita abstracciones prematuras.
- No introduzcas microservicios adicionales: FastAPI será inicialmente un backend modular único.
- No cambies tecnologías o decisiones de arquitectura sin explicar el motivo y actualizar `docs/ARCHITECTURE.md`.
- Si un requisito es ambiguo y afecta a seguridad, privacidad, datos o costes, pregunta antes de decidir. Para detalles menores, elige la solución más sencilla y documenta la decisión.
- No afirmes que una prueba, build, migración o despliegue ha funcionado si no se ha ejecutado y comprobado.
- No elimines datos, migraciones, ramas o recursos remotos sin autorización explícita.

## Calidad y seguridad

- Backend: tipado, validación Pydantic, manejo consistente de errores y separación por routers/services/repositories cuando aporte claridad.
- Base de datos: SQLAlchemy 2.x, Alembic, claves foráneas, índices y restricciones UNIQUE.
- Passwords: Argon2id mediante una librería mantenida; nunca guardar contraseñas en texto plano.
- Autenticación: tokens/cookies seguros; no almacenar secretos en el repositorio. Preferir cookies HttpOnly, Secure en producción y SameSite adecuado. Diseñar protección CSRF si se usan cookies autenticadas.
- Autorización: comprobar propietario/rol en backend en cada operación protegida.
- CORS restringido a orígenes configurados.
- Consultas parametrizadas/ORM; límites de paginación; límites de tamaño y tipo de archivo.
- Evitar XSS: sanitizar/renderizar texto enriquecido con una estrategia segura; no insertar HTML arbitrario.
- Rate limiting para login, registro, comprobación de nickname y comentarios; protección anti-spam.
- No registrar passwords, tokens, cookies, secretos ni datos sensibles.
- Nunca incluir datos privados en endpoints, SSR, sitemap, Open Graph o cachés públicos.
- Añadir pruebas de autorización y aislamiento de perfiles privados.

## Frontend

- Angular con TypeScript estricto y componentes standalone (salvo que la versión estable elegida recomiende otra configuración).
- UI accesible, responsive y Mobile First.
- Formularios reactivos con validación y mensajes breves bajo cada campo.
- La comprobación de nickname se dispara al perder el foco o con debounce; no hacer una petición por cada pulsación.
- La validación final siempre se repite en backend.
- Mantener español e inglés en archivos de traducción; no duplicar componentes por idioma.
- No mostrar URLs completas en botones de redes sociales.
- Mantener el estilo minimalista y el sistema visual compartido.

## SEO

- Verificar compatibilidad real de Angular SSR con el destino de despliegue elegido antes de implementarlo.
- Perfiles públicos y posts publicados: HTML renderizado con contenido esencial, title/description, canonical y Open Graph.
- Privados, borradores y rutas autenticadas: `noindex`, sin contenido sensible en HTML ni metadatos.
- Sitemap dinámico solo con perfiles públicos y posts publicados.
- `robots.txt`, canonical, datos estructurados Schema.org cuando sean correctos, imágenes optimizadas, Core Web Vitals y enlaces internos.
- No prometer indexación ni posicionamiento; Google decide si indexa.
- SEM/Google Ads no forma parte del MVP. No insertar publicidad sin decisión futura y consentimiento/cumplimiento aplicable.

## Git y entornos

Monorepo con ramas (ver D-008 en `docs/DECISIONS.md`):
- `develop`: integración de desarrollo.
- `preproduction`: validación previa (staging).
- `production`: producción (rama por defecto del remoto).
- `main`: sin uso por ahora; no participa en el flujo ni en el CI.

No hacer push, merge ni despliegue sin que el usuario lo solicite. Recomendar Pull Requests y CI. Configuración de cada entorno mediante variables y secretos independientes. No usar datos reales de producción en desarrollo.

## Docker

- Docker Compose para entorno local: Angular, FastAPI y PostgreSQL.
- Imágenes reproducibles, versiones fijadas y usuario no-root cuando sea viable.
- Healthchecks y volúmenes locales para PostgreSQL.
- Los archivos subidos localmente solo son para desarrollo; producción usará object storage.
- Nunca incluir `.env` real ni secretos en Git. Mantener `.env.example`.

## Documentación viva — obligatorio

Al terminar cada objetivo:
1. Actualiza `docs/ROADMAP.md` con estado y pruebas ejecutadas.
2. Actualiza `docs/ARCHITECTURE.md` si cambió alguna decisión técnica.
3. Actualiza `docs/API_SPECIFICATION.md` si cambian endpoints o contratos.
4. Actualiza `docs/DATABASE.md` si cambian entidades, campos, relaciones o migraciones.
5. Actualiza `docs/UI_UX_SPECIFICATION.md` si cambia una vista o interacción.
6. Registra decisiones importantes en `docs/DECISIONS.md` con fecha, contexto, decisión y consecuencias.
7. Indica archivos modificados, comandos ejecutados, resultado de pruebas y siguiente paso.

No inventes resultados. Si una prueba no pudo ejecutarse, indícalo y explica por qué.

## Formato de respuesta

Al cerrar cada tarea, responde de forma concisa:
- Qué se implementó.
- Archivos relevantes.
- Pruebas ejecutadas y resultado.
- Decisiones o limitaciones.
- Siguiente tarea recomendada.

No expliques conceptos básicos extensamente salvo que el usuario lo solicite.
