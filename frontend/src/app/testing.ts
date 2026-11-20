import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { EnvironmentProviders, Provider } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';

import { routes } from './app.routes';
import { csrfInterceptor, unauthorizedInterceptor } from './core/auth/auth.interceptors';
import { BundledTranslateLoader } from './core/i18n/language.service';

/** Providers comunes para tests: HTTP simulado, router real y traducciones en español. */
export function testProviders(): (Provider | EnvironmentProviders)[] {
  return [
    provideRouter(routes),
    provideHttpClient(withInterceptors([csrfInterceptor, unauthorizedInterceptor])),
    provideHttpClientTesting(),
    provideTranslateService({
      loader: provideTranslateLoader(BundledTranslateLoader),
      fallbackLang: 'es',
      lang: 'es',
    }),
  ];
}

export const ME = {
  id: '1',
  email: 'ana@example.com',
  role: 'user' as const,
  profile: {
    nickname: 'ana-dev',
    display_name: 'Ana García',
    first_name: 'Ana',
    last_name: 'García',
    visibility: 'public' as const,
    preferred_language: 'es' as const,
  },
};
