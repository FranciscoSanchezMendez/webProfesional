import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { CookieStore } from '../http/cookies';
import { AUTH_API, AuthService } from './auth.service';

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
export const CSRF_HEADER = 'X-CSRF-Token';
/** Con HTTPS el backend usa el prefijo __Host- (D-015). */
const CSRF_COOKIES = ['__Host-pp_csrf', 'pp_csrf'];

function isApi(url: string): boolean {
  return url.startsWith('/api/');
}

/** Copia el token CSRF de la cookie legible a la cabecera en peticiones que modifican datos (D-016). */
export const csrfInterceptor: HttpInterceptorFn = (req, next) => {
  if (!isApi(req.url) || SAFE_METHODS.has(req.method)) {
    return next(req);
  }
  const cookies = inject(CookieStore);
  const token = CSRF_COOKIES.map((name) => cookies.get(name)).find(Boolean);
  return next(token ? req.clone({ setHeaders: { [CSRF_HEADER]: token } }) : req);
};

/** Un 401 de la API significa que la sesión ya no es válida. */
export const unauthorizedInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  return next(req).pipe(
    catchError((error: unknown) => {
      const isLogin = req.url === `${AUTH_API}/login`;
      if (error instanceof HttpErrorResponse && error.status === 401 && isApi(req.url) && !isLogin) {
        auth.markAnonymous();
      }
      return throwError(() => error);
    }),
  );
};
