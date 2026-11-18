# Requisitos funcionales — PersonalProfile

## 1. Cuentas y autenticación

### Registro
Campos mínimos:
- Nombre.
- Apellidos.
- Nickname público único.
- Fecha de nacimiento.
- Ubicación/localidad.
- Puesto de trabajo u oficio.
- Email.
- Contraseña y confirmación.
- Visibilidad inicial: pública (por defecto) o privada.
- Idioma de interfaz: español o inglés.

Reglas:
- Email único, normalizado y validado.
- Nickname único, normalizado a minúsculas para comparación y URL.
- Nickname: 3–30 caracteres, letras ASCII, números y guion; no empezar/terminar con guion. Aceptar visualización con `@` en URL, pero almacenar sin `@`.
- Lista de rutas reservadas (login, register, about, contact, faq, admin, api, assets, etc.) no disponible como nickname.
- Mensajes de validación pequeños bajo el campo; errores en rojo y disponibilidad correcta en verde.
- Al cambiar de campo, consultar disponibilidad del nickname. Aplicar debounce si se implementa comprobación mientras escribe.
- La comprobación no reserva el nickname. La restricción UNIQUE en PostgreSQL y el alta transaccional resuelven carreras.
- Tras registro válido, iniciar sesión automáticamente.
- No exigir verificación de correo en MVP.
- Google Login y recuperación de contraseña quedan fuera del MVP; mostrar como “Próximamente” solo si se desea, sin simular que funcionan.

### Login
- Email + contraseña.
- Mensajes de error genéricos para no revelar si un email existe.
- Rate limiting y protección frente a fuerza bruta.
- Logout que invalida/limpia sesión de forma segura.
- Persistencia de sesión según política segura y configurable.

### Cuenta y seguridad
- El usuario puede cambiar visibilidad a pública/privada.
- Puede editar datos, avatar, cabecera, idioma, biografía y enlaces.
- La fecha de nacimiento no se publica. Mostrar edad calculada solo si el usuario lo permite.
- No implementar recuperación de contraseña en MVP.
- No implementar verificación de email en MVP.
- No permitir que el usuario se asigne el rol admin.

## 2. Perfil público/privado

### Público
- Acceso anónimo permitido a `/@nickname`.
- SSR/HTML y metadatos contienen solo información pública.
- Perfil y posts publicados elegibles para sitemap e indexación.

### Privado
- Visitante sin sesión: pantalla/modal informativo con acceso a login/registro.
- Tras login: cualquier usuario autenticado puede ver el perfil privado, según la decisión adoptada para el MVP.
- No incluir contenido del perfil en respuestas anónimas, SSR, metadata, sitemap, Open Graph ni caché pública.
- El propietario autenticado siempre puede ver y editar su perfil.
- No implementar solicitudes de acceso ni listas de seguidores.

### Perfil del creador
- `/` muestra el perfil del creador configurado por variable `CREATOR_USER_ID` o mecanismo equivalente seguro.
- El creador también dispone de `/@nickname`.
- La cuenta se crea como usuario normal y su `role` se cambia manualmente en PostgreSQL a `admin`.
- No existe endpoint de asignación de rol.

## 3. Enlaces externos
- CRUD de enlaces por propietario.
- Tipos iniciales: LinkedIn, Tecnoempleo, InfoJobs, Indeed, GitHub, YouTube y web personal.
- Detectar plataforma mediante hostname/URL validada.
- El usuario pega la URL; el botón muestra icono y nombre del servicio, nunca la URL completa.
- Permitir varios enlaces, ordenarlos y eliminarlos.
- Abrir enlaces externos de forma segura (`rel="noopener noreferrer"` cuando corresponda).
- No permitir esquemas peligrosos como `javascript:` o `data:`.
- Para dominios no reconocidos, usar categoría “Web personal” o “Otro” con icono genérico, sin iconos personalizados en MVP.

## 4. Publicaciones
- Crear, editar, publicar, despublicar, destacar/fijar y eliminar.
- Campos: título, texto/contenido, imagen principal, imágenes secundarias, enlaces opcionales, etiquetas opcionales, fecha de creación/actualización y estado.
- Una imagen principal y múltiples imágenes secundarias.
- Vista de detalle con carrusel/galería.
- Tarjeta resumen en perfil.
- Solo el propietario administra sus publicaciones.
- Validar formatos y tamaño de archivos; generar nombres aleatorios y metadatos seguros.
- Publicaciones en borrador no visibles públicamente.
- La privacidad del perfil prevalece sobre la publicación.

## 5. Comentarios
- Comentarios habilitados por publicación con opción de desactivar.
- Visitante anónimo puede comentar proporcionando nombre, apellidos y nombre visible, sin crear cuenta.
- Usuario registrado comenta usando identidad de su cuenta.
- Hilos: permitir respuestas a un comentario; limitar inicialmente a un nivel de respuesta o definir profundidad máxima para evitar complejidad.
- El propietario del perfil puede eliminar comentarios de sus publicaciones.
- Autor puede eliminar su propio comentario si está autenticado; para anónimos no ofrecer edición/eliminación en MVP salvo que se diseñe un mecanismo verificable.
- Protección anti-spam: rate limit por IP/identificador, honeypot y límites de longitud; CAPTCHA solo si el abuso lo justifica.
- Escapar/sanitizar contenido para prevenir XSS.
- No hay sistema de denuncias en MVP.

## 6. Likes
- Solo usuarios autenticados.
- Un like por usuario y publicación (restricción UNIQUE user_id + post_id).
- Permitir alternar like/unlike.
- No mostrar controles de like a visitantes anónimos; pueden ver el contador público.
- No permitir likes en borradores o posts inaccesibles por privacidad.

## 7. Panel de usuario
- Edición de datos personales/profesionales.
- Cambiar privacidad.
- Gestionar enlaces.
- Gestionar posts.
- Gestionar comentarios de sus posts.
- Cambiar idioma de interfaz.
- Desactivar temporalmente perfil/cuenta (definir comportamiento: perfil no visible; datos conservados). La reactivación vuelve a restaurar visibilidad configurada.
- No incluir personalización de colores, temas o estructura visual.

## 8. Panel de administrador
- Solo `role=admin`, asignado manualmente en base de datos.
- Listado básico de usuarios con paginación.
- Sin buscador en MVP.
- No permitir crear administradores desde interfaz/API.
- Sin herramientas de moderación global en MVP.

## 9. Páginas globales
- `/login`, `/register`, `/about`, `/contact`, `/faq`.
- Header común sin enlaces About/Contact/FAQ.
- Footer común con información básica, mención del creador y enlaces a esas páginas.
- Página de detalle de post mantiene header/footer, botón volver y no muestra los enlaces sociales del perfil.

## 10. Idiomas y accesibilidad
- Interfaz español/inglés.
- Contenido de perfil y publicaciones en idioma libre elegido por usuario.
- Responsive Mobile First, modo claro/oscuro.
- Navegación por teclado, labels, contraste, foco visible y textos alternativos para imágenes.

## 11. Fuera de alcance del MVP
- OAuth Google real.
- Recuperación de contraseña por email.
- Verificación de email.
- Planes premium, pagos y publicidad.
- Solicitudes de acceso a perfiles privados.
- Denuncias y moderación global.
- Mensajería privada.
- Búsqueda avanzada de usuarios.
- Analytics no esenciales.
- Aplicaciones móviles nativas.
