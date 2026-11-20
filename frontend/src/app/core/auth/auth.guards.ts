import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID, inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

// Nota: inject() solo funciona antes del primer `await` (después se pierde el contexto de inyección).

/** Rutas solo para visitantes (login, registro): con sesión se redirige al inicio. */
export const guestGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  await auth.ensureLoaded();
  return auth.status() === 'authenticated' ? router.parseUrl('/') : true;
};

/**
 * Rutas que requieren sesión. En SSR no se conoce la sesión: esas rutas deben usar
 * RenderMode.Client y cargar sus datos desde el navegador (la API vuelve a autorizar).
 */
export const authGuard: CanActivateFn = async (_route, state) => {
  if (!isPlatformBrowser(inject(PLATFORM_ID))) {
    return true;
  }
  const auth = inject(AuthService);
  const router = inject(Router);
  await auth.ensureLoaded();
  if (auth.status() === 'authenticated') {
    return true;
  }
  return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

/** Evita redirecciones abiertas: solo rutas internas absolutas. */
export function safeReturnUrl(value: string | null | undefined): string {
  return value && value.startsWith('/') && !value.startsWith('//') && !value.includes('\\')
    ? value
    : '/';
}
