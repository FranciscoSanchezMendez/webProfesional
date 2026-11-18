# Modelo de datos inicial — PostgreSQL

El esquema es una propuesta inicial. Claude debe convertirlo en modelos SQLAlchemy y migraciones Alembic, revisar constraints e índices y actualizar este documento al cambiarlo.

## Estado implementado

| Migración | Fecha | Contenido |
|---|---|---|
| `f9b83d8d5ca7` (`backend/alembic/versions/2026_11_18_2107-…`) | 2026-11-18 | Tablas `users` y `profiles` |
| `8994bd5c2527` (`backend/alembic/versions/2026_11_18_2223-…`) | 2026-11-18 | Tablas `sessions` y `rate_limits` |

Modelos: `backend/app/models/{user,profile,enums}.py`. Repositorio: `backend/app/repositories/users.py`.

### Convenciones aplicadas
- PK `UUID` generado en aplicación (`uuid4`).
- `created_at`/`updated_at`: `timestamptz`, `DEFAULT now()`; `updated_at` lo actualiza el ORM.
- Enumerados como `VARCHAR` + `CHECK` (no ENUM nativo de PostgreSQL); ver D-010.
- Nombres de restricciones deterministas: `pk_<tabla>`, `uq_<tabla>_<col>`, `fk_<tabla>_<col>_<ref>`,
  `ck_<tabla>_<nombre>`, `ix_<tabla>_<col>`.

### `users` (implementada)
| Columna | Tipo | Restricciones |
|---|---|---|
| id | uuid | PK |
| email | varchar(254) | NOT NULL, `uq_users_email`, `ck_users_email_normalized` (`email = lower(btrim(email))`) |
| password_hash | varchar(255) | NOT NULL (Argon2id en Fase 2) |
| role | varchar(5) | NOT NULL, DEFAULT `user`, `ck_users_role` IN (`user`,`admin`) |
| is_active | boolean | NOT NULL, DEFAULT true (bloqueo de cuenta por sistema/admin) |
| last_login_at | timestamptz | NULL |
| created_at, updated_at | timestamptz | NOT NULL, DEFAULT now() |

### `profiles` (implementada)
| Columna | Tipo | Restricciones |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | NOT NULL, `uq_profiles_user_id` (1:1), FK `users.id` ON DELETE CASCADE |
| nickname | varchar(30) | NOT NULL, `uq_profiles_nickname`, `ck_profiles_nickname_format` (`^[a-z0-9]([a-z0-9-]{1,28})[a-z0-9]$`) |
| first_name, last_name, display_name | varchar(100) | NOT NULL |
| birth_date | date | NOT NULL — **privada** |
| location, job_title | varchar(120) | NULL |
| biography | text | NULL (límite de longitud en la API, Fase 4) |
| avatar_key, cover_key | varchar(255) | NULL (claves de object storage, no URLs) |
| visibility | varchar(7) | NOT NULL, DEFAULT `public`, `ck_profiles_visibility` |
| show_age | boolean | NOT NULL, DEFAULT false |
| is_deactivated | boolean | NOT NULL, DEFAULT false (desactivación temporal por el usuario) |
| preferred_language | varchar(2) | NOT NULL, DEFAULT `es`, `ck_profiles_preferred_language` |
| created_at, updated_at | timestamptz | NOT NULL, DEFAULT now() |

### `sessions` (implementada, Fase 2)
| Columna | Tipo | Restricciones |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | NOT NULL, FK `users.id` ON DELETE CASCADE, índice `ix_sessions_user_id` |
| token_hash | varchar(64) | NOT NULL, `uq_sessions_token_hash` — SHA-256 del token de la cookie |
| csrf_token_hash | varchar(64) | NOT NULL — SHA-256 del token CSRF |
| persistent | boolean | NOT NULL — `true` si el usuario marcó «Recordarme» |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| expires_at | timestamptz | NOT NULL, índice `ix_sessions_expires_at` |

Los tokens en claro solo existen en la cookie del navegador. Sin IP ni user-agent (minimización de datos).

### `rate_limits` (implementada, Fase 2)
| Columna | Tipo | Restricciones |
|---|---|---|
| key | varchar(100) | PK (compuesta) — `<acción>:<sha256(IP o email)>` |
| window_start | timestamptz | PK (compuesta) — inicio de la ventana fija |
| count | integer | NOT NULL |

No guarda IPs ni emails en claro. Limpieza de filas antiguas y de sesiones caducadas:
`purge_expired()` / `purge_expired_sessions()`, pendientes de programar como tarea (Fase 10).

Nicknames reservados: lista en código (`app/core/reserved.py`), validada en backend; no hay tabla.
Las tablas siguientes de este documento siguen siendo propuesta.

## Entidades (propuesta inicial)

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
- is_suspended/deactivated: implementado como `is_deactivated` (ver "Estado implementado").
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
