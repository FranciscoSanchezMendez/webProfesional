# PROJECT_CONTEXT — PersonalProfile

## Qué queremos construir

PersonalProfile es una plataforma web donde cualquier persona puede crear una página personal-profesional pública o privada, sin conocimientos técnicos. Combina portfolio profesional, tarjeta de presentación digital y escaparate de proyectos.

Cada usuario dispone de una URL del tipo:

`https://<dominio>/@<nickname>`

La raíz `/` corresponde al perfil del creador de la plataforma. El creador tendrá un perfil normal y, además, permisos de administrador si su rol se modifica manualmente en PostgreSQL.

## Usuarios y visitantes

- Visitante anónimo: puede ver perfiles públicos, publicaciones públicas y comentar proporcionando nombre, apellidos y nombre visible.
- Usuario registrado: puede gestionar su propio perfil, enlaces, publicaciones, comentarios, dar/quitar likes y ver perfiles privados.
- Propietario del perfil: puede editar su perfil, gestionar sus enlaces/posts, eliminar comentarios de sus publicaciones y activar/desactivar comentarios por publicación.
- Administrador: puede consultar un listado paginado de usuarios. En esta primera versión no hay panel de moderación, buscador ni herramientas para asignar roles.

## Privacidad de perfiles

- Público: cualquier visitante, con o sin sesión, puede ver el perfil y sus publicaciones publicadas.
- Privado: solo usuarios autenticados pueden ver el perfil y su contenido. Los visitantes anónimos ven una pantalla/modal informativo que invita a iniciar sesión. Tras autenticarse, pueden acceder.
- La privacidad se aplica en backend, no solo ocultando componentes en Angular.
- Los perfiles privados no deben incluir contenido personal en HTML renderizado, metadatos, sitemap ni endpoints públicos.
- El propietario siempre puede ver y editar su propio perfil.

## Experiencia principal

Página de perfil en una sola columna vertical:
1. Header global: marca; si hay sesión, avatar y nombre/nickname con acceso al menú; si no, botones de login y registro.
2. Cabecera visual con imagen de fondo y avatar.
3. Datos esenciales: nombre completo, oficio/cargo, localidad, edad si el usuario permite mostrarla y biografía.
4. Enlaces externos: botones/iconos reconocibles, sin mostrar URL. Detección automática de LinkedIn, Tecnoempleo, InfoJobs, Indeed, GitHub, YouTube y web personal. El usuario añade varios y puede ordenarlos.
5. Publicaciones en tarjetas con imagen principal, título, extracto y fecha.
6. Footer común con información de la plataforma, About, Contact, FAQ y mención del creador.

La edición del perfil solo aparece al propietario autenticado.

## Posts

Cada publicación tiene título, texto, fecha, imagen principal, imágenes secundarias para galería/carrusel, enlaces externos opcionales, etiquetas opcionales, estado borrador/publicado y opción de destacar/fijar.

Detalle del post:
- Mantiene el header global.
- Flecha para volver al perfil.
- No muestra el bloque de enlaces del perfil.
- Muestra contenido completo, galería/carrusel y enlaces.
- Incluye likes (solo registrados) y comentarios en hilos.
- El propietario puede borrar comentarios de sus publicaciones y desactivar comentarios por post.
- Autor registrado identificado mediante su cuenta; autor anónimo identificado por nombre visible y datos proporcionados.

## Diseño

- Estética minimalista profesional, basada en la primera referencia visual elegida.
- Diseño responsive Mobile First.
- Modo claro y oscuro.
- Estructura visual común para todos los usuarios; no se personalizan temas, colores ni layouts.
- Personalización permitida: avatar, imagen de cabecera, biografía, datos profesionales, enlaces y publicaciones.
- Botones de enlaces con icono y nombre del servicio, diseño adaptable a lista o grid de dos columnas según cantidad.
- No mostrar About/Contact/FAQ en el header; únicamente en footer.

## Idiomas

- Interfaz traducida a español e inglés.
- El idioma de interfaz se puede elegir y recordar.
- El contenido del usuario (biografía, publicaciones, comentarios) no se traduce automáticamente ni requiere duplicar textos. Cada usuario escribe en el idioma que prefiera.
- No inferir idioma del contenido a partir del idioma de la interfaz.

## Objetivo técnico y didáctico

Construir una aplicación real, mantenible y desplegable:
- Backend: Python + FastAPI.
- Frontend: Angular + TypeScript.
- Persistencia: PostgreSQL.
- ORM/migraciones: SQLAlchemy 2.x + Alembic.
- Validación: Pydantic.
- Contenedores: Docker y Docker Compose.
- CI/CD: GitHub Actions.
- Desarrollo por incrementos verticales, probando cada funcionalidad.
- Explicaciones técnicas breves y prácticas; prioridad a entregar el producto.

## Principios

1. No sobredimensionar la arquitectura para el objetivo inicial de al menos 10 usuarios.
2. No introducir microservicios independientes sin necesidad: disponibilidad de nickname será un endpoint del backend.
3. No guardar binarios de imágenes en PostgreSQL ni en filesystem efímero de producción.
4. No confiar en validaciones del frontend para seguridad o integridad.
5. Privacidad y permisos siempre comprobados en backend.
6. Mantener documentación y decisiones actualizadas durante el desarrollo.
7. No asumir que un free tier es apto para producción permanente: documentar límites, backups y riesgos.
