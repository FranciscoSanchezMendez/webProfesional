import { RenderMode, ServerRoute } from '@angular/ssr';

/**
 * Todas las rutas se renderizan en servidor por petición (contenido dinámico, idioma y tema
 * dependen de cookies). Las rutas desconocidas responden 404.
 */
export const serverRoutes: ServerRoute[] = [
  ...['', 'login', 'register', 'about', 'contact', 'faq'].map(
    (path): ServerRoute => ({ path, renderMode: RenderMode.Server }),
  ),
  { path: '**', renderMode: RenderMode.Server, status: 404 },
];
