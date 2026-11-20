import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { TitleStrategy, provideRouter, withComponentInputBinding } from '@angular/router';
import { provideTranslateLoader, provideTranslateService } from '@ngx-translate/core';

import { routes } from './app.routes';
import { csrfInterceptor, unauthorizedInterceptor } from './core/auth/auth.interceptors';
import {
  BundledTranslateLoader,
  DEFAULT_LANGUAGE,
  LanguageService,
} from './core/i18n/language.service';
import { SeoTitleStrategy } from './core/i18n/seo-title.strategy';
import { ThemeService } from './core/theme/theme.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    { provide: TitleStrategy, useClass: SeoTitleStrategy },
    provideClientHydration(withEventReplay()),
    provideHttpClient(withFetch(), withInterceptors([csrfInterceptor, unauthorizedInterceptor])),
    provideTranslateService({
      loader: provideTranslateLoader(BundledTranslateLoader),
      fallbackLang: DEFAULT_LANGUAGE,
    }),
    // Idioma y tema se resuelven antes del primer render (también en SSR) para evitar parpadeos.
    provideAppInitializer(() => {
      inject(ThemeService).init();
      return inject(LanguageService).init();
    }),
  ],
};
