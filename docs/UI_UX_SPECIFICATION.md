# Especificación UI/UX

> **Pendiente:** PROJECT_CONTEXT.md cita una "primera referencia visual elegida" que no está en el
> repositorio. Hasta incorporarla, la interfaz usa un diseño minimalista neutro basado en tokens CSS
> (`frontend/src/styles.scss`). Aplicar la referencia = cambiar tokens, no componentes.

## Principios
- Mobile first: estilos base para móvil, ampliación con `min-width` (40rem tablet, 48rem escritorio).
- Una sola columna; contenedor máximo 64rem con margen lateral de 1rem.
- Estructura visual común para todos los usuarios; sin temas personalizados.
- Accesibilidad: enlace "Saltar al contenido", foco visible (`:focus-visible`), etiquetas en todos los
  campos, `aria-invalid` + `aria-describedby` hacia el mensaje de error, objetivos táctiles ≥ 2.75rem,
  foco al primer campo inválido tras un envío fallido.

## Tokens (tema claro / oscuro)
| Token | Uso |
|---|---|
| `--color-bg` | fondo exterior (bandas laterales a los lados del contenido) |
| `--color-content` | panel de contenido (zona donde se muestran los datos) |
| `--color-surface`, `--color-surface-muted` | formularios, menús e inputs; hover |
| `--color-chrome`, `--color-chrome-hover`, `--color-chrome-border` | fondo de cabecera y pie, hover y bordes sobre ellos |
| `--color-on-chrome`, `--color-on-chrome-muted` | texto sobre cabecera y pie |
| `--color-text`, `--color-text-muted` | texto principal y secundario |
| `--color-border` | bordes |
| `--color-primary`, `--color-primary-hover`, `--color-on-primary` | acciones principales |
| `--color-danger`, `--color-success` | errores (rojo) y confirmaciones (verde) |
| `--space-1…6`, `--radius`, `--radius-pill`, `--shadow` | espaciado, radios, sombra |

Tema: `Sistema` (sigue `prefers-color-scheme`), `Claro` u `Oscuro`; se elige en el footer y se guarda en la
cookie `pp_theme`, que el SSR lee para pintar ya el tema correcto (sin parpadeo).

## Shell

### Estructura (2026-11-20)
```text
┌──────────────── cabecera (--color-chrome, ancho completo) ────────────────┐
│ fondo │ ┌──────── panel de contenido (--color-content) ────────┐ │ fondo │
│ (bg)  │ │ mismos márgenes laterales que el contenido de la      │ │ (bg)  │
│       │ │ cabecera (.container: máx. 64rem, 1rem lateral)       │ │       │
│       │ └───────────────────────────────────────────────────────┘ │       │
└──────────────── pie (--color-chrome, ancho completo) ─────────────────────┘
```
- El panel ocupa todo el alto entre cabecera y pie, sin franjas de separación verticales, con borde
  lateral fino. Las páginas no añaden su propio contenedor: lo aporta el panel (`app.html`).
- Cabecera y pie usan un tono pizarra propio en ambos temas (oscuro en el tema claro; intermedio, más
  claro que el fondo, en el tema oscuro) para enmarcar el contenido.

- **Header**: marca (enlace a `/`) a la izquierda. A la derecha:
  - sin sesión: botones "Iniciar sesión" (secundario) y "Crear cuenta" (principal);
  - con sesión: avatar con iniciales + nombre visible y `@nickname` (en móvil solo el avatar); abre un menú
    (popover nativo: cierra con Escape o clic fuera) con "Cerrar sesión";
  - mientras se resuelve la sesión (y siempre en el HTML del SSR): hueco reservado, sin botones, para no
    mostrar un estado incorrecto ni provocar saltos de maquetación.
  - Sin enlaces About/Contact/FAQ.
- **Footer**: marca, lema, mención del creador (enlace a `/`), enlaces Acerca de / Contacto / Preguntas
  frecuentes, selector de idioma (nombres nativos: Español / English) y de tema.

## Páginas (Fase 3)
| Ruta | Contenido | Indexación |
|---|---|---|
| `/` | Marcador: título, lema, saludo si hay sesión. En Fase 4: perfil del creador | sí |
| `/login` | Email, contraseña, «Recordarme», enlace a registro | `noindex` |
| `/register` | Formulario de registro, enlace a login | `noindex` |
| `/about`, `/contact`, `/faq` | Marcadores "Contenido en preparación" | sí |
| otra | 404 con enlace al inicio (HTTP 404 en SSR) | `noindex` |

`/login` y `/register` redirigen a `/` si ya hay sesión. Tras login se vuelve a `returnUrl` (solo rutas
internas) o a `/`; tras registro, a `/`.

## Formularios
- Mensajes breves bajo cada campo, en rojo, visibles tras tocar el campo o al enviar.
- Validación en cliente espejo de la API (la API vuelve a validar todo).
- Registro, en este orden: nombre · apellidos (2 columnas desde tablet), nickname, fecha de nacimiento
  (con aviso "No se mostrará públicamente"), localidad · puesto, email, contraseña · repetir contraseña,
  visibilidad (radio público/privado), idioma de la interfaz.
- Nickname: se comprueba **al perder el foco** (una petición), muestra "Comprobando…" y después
  "Nickname disponible" en verde o el error (en uso / reservado / formato). Muestra la URL resultante
  `/@nickname` normalizada.
- Errores del servidor: 409 `email_taken`/`nickname_taken` → bajo su campo; 422 → "Valor no válido" bajo el
  campo indicado en `loc`; resto → aviso general sobre el formulario (`role="alert"`).
- Login: un único mensaje genérico ("Email o contraseña incorrectos.") y aviso específico para 429.
- Contraseña: 7–30 caracteres (D-022); la pista bajo el campo muestra el mínimo.
- Botón de envío deshabilitado y con texto "Enviando…" durante la petición.

## Idioma
- Interfaz en español e inglés (`frontend/src/app/core/i18n/{es,en}.ts`; el compilador exige las mismas
  claves en ambos).
- Detección: cookie `pp_lang` → idioma del navegador (`Accept-Language` en SSR) → español.
- Al iniciar sesión o registrarse se aplica `preferred_language` de la cuenta.
- El cambio en el footer se recuerda en cookie. (Sincronizarlo con el perfil llegará con la edición, Fase 4.)
- Títulos de pestaña traducidos: `<página> · PersonalProfile`.
