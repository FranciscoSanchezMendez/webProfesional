import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, REQUEST, inject, signal } from '@angular/core';
import { TranslateLoader, TranslateService, TranslationObject } from '@ngx-translate/core';
import { Observable, from, map } from 'rxjs';

import { CookieStore } from '../http/cookies';

export const LANGUAGES = ['es', 'en'] as const;
export type Language = (typeof LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = 'es';
export const LANGUAGE_COOKIE = 'pp_lang';

export function isLanguage(value: unknown): value is Language {
  return typeof value === 'string' && (LANGUAGES as readonly string[]).includes(value);
}

/** Traducciones empaquetadas (import dinámico): funcionan igual en SSR y navegador, sin HTTP. */
export class BundledTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<TranslationObject> {
    const load =
      lang === 'en' ? import('./en').then((m) => m.en) : import('./es').then((m) => m.es);
    return from(load).pipe(map((t) => t as unknown as TranslationObject));
  }
}

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private readonly translate = inject(TranslateService);
  private readonly cookies = inject(CookieStore);
  private readonly document = inject(DOCUMENT);
  private readonly request = inject(REQUEST, { optional: true });
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  readonly current = signal<Language>(DEFAULT_LANGUAGE);

  /** Orden: cookie elegida por el usuario → idioma del navegador → español. */
  init(): Observable<unknown> {
    return this.apply(this.detect());
  }

  /** Cambio explícito del usuario: se recuerda en una cookie. */
  use(lang: Language): Observable<unknown> {
    this.cookies.set(LANGUAGE_COOKIE, lang);
    return this.apply(lang);
  }

  private apply(lang: Language): Observable<unknown> {
    this.current.set(lang);
    this.document.documentElement.lang = lang;
    return this.translate.use(lang);
  }

  private detect(): Language {
    const saved = this.cookies.get(LANGUAGE_COOKIE);
    if (isLanguage(saved)) {
      return saved;
    }
    const preferred = this.isBrowser
      ? [...(this.document.defaultView?.navigator.languages ?? [])]
      : (this.request?.headers.get('accept-language') ?? '').split(',');
    for (const entry of preferred) {
      const code = entry.trim().slice(0, 2).toLowerCase();
      if (isLanguage(code)) {
        return code;
      }
    }
    return DEFAULT_LANGUAGE;
  }
}
