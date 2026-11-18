import { RenderMode, ServerRoute } from '@angular/ssr';

// Las rutas públicas (p. ej. /@nickname) son dinámicas: se renderizan en servidor por petición.
export const serverRoutes: ServerRoute[] = [
  {
    path: '**',
    renderMode: RenderMode.Server,
  },
];
