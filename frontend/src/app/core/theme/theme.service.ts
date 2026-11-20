import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

import { CookieStore } from '../http/cookies';

export const THEMES = ['system', 'light', 'dark'] as const;
export type Theme = (typeof THEMES)[number];
export const THEME_COOKIE = 'pp_theme';

/**
 * El tema se guarda en cookie para que el SSR pinte ya el correcto (sin parpadeo).
 * 'system' = sin atributo: manda prefers-color-scheme.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly cookies = inject(CookieStore);

  readonly current = signal<Theme>('system');

  init(): void {
    const saved = this.cookies.get(THEME_COOKIE);
    this.apply(saved === 'light' || saved === 'dark' ? saved : 'system');
  }

  use(theme: Theme): void {
    if (theme === 'system') {
      this.cookies.delete(THEME_COOKIE);
    } else {
      this.cookies.set(THEME_COOKIE, theme);
    }
    this.apply(theme);
  }

  private apply(theme: Theme): void {
    this.current.set(theme);
    const root = this.document.documentElement;
    if (theme === 'system') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', theme);
    }
  }
}
