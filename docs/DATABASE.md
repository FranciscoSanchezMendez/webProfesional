# Modelo de datos inicial — PostgreSQL

El esquema es una propuesta inicial. Claude debe convertirlo en modelos SQLAlchemy y migraciones Alembic, revisar constraints e índices y actualizar este documento al cambiarlo.

## Entidades

### users
- id: UUID PK.
- email: varchar, NOT NULL, UNIQUE, normalizado.
- password_hash: varchar, NOT NULL.
- role: enum/string (`user`, `admin`), default `user`.
- is_active: boolean, default true.
- created_at, updated_at: timestamptz.
- last_login_at: timestamptz nullable.

### profiles
- id: UUID PK.
- user_id: UUID FK users.id UNIQUE.
- nickname: varchar NOT NULL, UNIQUE, normalizado lowercase.
- first_name, last_name: varchar NOT NULL.
- display_name: varchar NOT NULL.
- birth_date: date NOT NULL, privada.
- location: varchar nullable.
- job_title: varchar nullable.
- biography: text nullable.
- avatar_key: varchar nullable.
- cover_key: varchar nullable.
- visibility: enum (`public`, `private`), default `public`.
- show_age: boolean default false.
- is_suspended/deactivated: boolean según definición final.
- preferred_language: enum (`es`, `en`).
- created_at, updated_at.

### profile_links
- id UUID PK.
- profile_id FK profiles.id.
- platform: enum/string controlado (`linkedin`, `tecnoempleo`, `infojobs`, `indeed`, `github`, `youtube`, `website`, `other`).
- url: text NOT NULL.
- sort_order: integer NOT NULL.
- created_at, updated_at.
- Índice por profile_id, sort_order.

### posts
- id UUID PK.
- profile_id FK profiles.id.
- title varchar NOT NULL.
- slug varchar NOT NULL.
- body text NOT NULL.
- excerpt text nullable.
- status enum (`draft`, `published`).
- is_featured boolean default false.
- comments_enabled boolean default true.
- published_at timestamptz nullable.
- created_at, updated_at.
- UNIQUE(profile_id, slug).
- Índices profile_id/status/published_at.

### post_images
- id UUID PK.
- post_id FK posts.id.
- object_key varchar NOT NULL.
- alt_text varchar nullable.
- sort_order integer NOT NULL.
- is_cover boolean default false.
- width/height integer nullable.
- created_at.
- Un post puede tener una imagen de portada y varias imágenes adicionales. Aplicar constraint o lógica transaccional para una sola portada por post.

### post_links
- id UUID PK.
- post_id FK posts.id.
- label varchar NOT NULL.
- url text NOT NULL.
- sort_order integer.
- created_at.

### comments
- id UUID PK.
- post_id FK posts.id.
- parent_id UUID FK comments.id nullable.
- user_id UUID FK users.id nullable.
- guest_first_name varchar nullable.
- guest_last_name varchar nullable.
- guest_display_name varchar nullable.
- body text NOT NULL.
- created_at, updated_at.
- deleted_at nullable o soft delete.
- Constraint lógica: comentario registrado tiene user_id; anónimo tiene los tres campos guest.
- Limitar profundidad de hilo (recomendación inicial: un nivel de respuesta).
- Índices post_id/created_at y parent_id.

### post_likes
- id UUID PK.
- post_id FK posts.id.
- user_id FK users.id.
- created_at.
- UNIQUE(post_id, user_id).

### reserved_nicknames
Opcional: tabla de rutas/nicknames reservados gestionada por migraciones o configuración. Debe existir una comprobación de backend y test. No permitir colisión con rutas globales.

## Relaciones principales

- users 1:1 profiles.
- profiles 1:N profile_links.
- profiles 1:N posts.
- posts 1:N post_images.
- posts 1:N post_links.
- posts 1:N comments.
- comments 1:N replies (parent_id).
- posts N:M users mediante post_likes.

## Reglas de privacidad y borrado

- Las consultas de perfil deben filtrar visibilidad antes de devolver información.
- El acceso de visitante a perfil privado devuelve respuesta que no contiene datos del perfil (401/403 o vista controlada; decidir contrato API).
- Borrado de cuenta: definir política de anonimización/borrado en fase posterior; no dejar relaciones huérfanas.
- Eliminar post debe eliminar comentarios/likes/imágenes asociadas de forma controlada y borrar objetos del storage.
- Al borrar una imagen, eliminar el objeto del bucket tras confirmar que no se referencia en otra entidad.

## Datos personales

- Fecha de nacimiento siempre privada; calcular edad en backend o frontend con cuidado de zona/fecha.
- No incluir birth_date en DTO público.
- Dirección debe ser ubicación general (localidad/ciudad), no dirección postal.
- Establecer retención y borrado conforme a RGPD antes del lanzamiento público.
