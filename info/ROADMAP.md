# Roadmap de implementación

Estados iniciales: TODO. Claude debe actualizar este archivo después de cada hito.

## Fase 0 — Repositorio y entorno
- [ ] Crear monorepo y ramas `develop`, `staging`, `main`.
- [ ] Añadir `.gitignore`, `.env.example`, README.
- [ ] Docker Compose: Angular, FastAPI, PostgreSQL.
- [ ] Healthchecks y conexión frontend-backend.
- [ ] CI inicial: lint/build/tests.
**Criterio de salida:** levantar el entorno local con un comando y ejecutar checks verdes.

## Fase 1 — Backend base y modelo
- [ ] Configuración Pydantic por entorno.
- [ ] SQLAlchemy y Alembic.
- [ ] Modelos User/Profile.
- [ ] Migración inicial.
- [ ] Tests de repositorio y migración.
**Criterio:** DB creada y migraciones reproducibles.

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
