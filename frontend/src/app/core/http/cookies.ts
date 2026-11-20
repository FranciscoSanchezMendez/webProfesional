import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, REQUEST, inject } from '@angular/core';

/** Lee cookies en el navegador (document.cookie) y en SSR (cabecera Cookie de la petición). */
@Injectable({ providedIn: 'root' })
export class CookieStore {
  private readonly document = inject(DOCUMENT);
  private readonly request = inject(REQUEST, { optional: true });
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  get(name: string): string | null {
    const raw = this.isBrowser ? this.document.cookie : (this.request?.headers.get('cookie') ?? '');
    for (const part of raw.split(';')) {
      const [key, ...value] = part.trim().split('=');
      if (key === name) {
        return decodeURIComponent(value.join('='));
      }
    }
    return null;
  }

  /** Cookie de preferencia (no sensible). Solo en el navegador. */
  set(name: string, value: string, maxAgeDays = 365): void {
    if (!this.isBrowser) {
      return;
    }
    const secure = this.document.location.protocol === 'https:' ? '; Secure' : '';
    const maxAge = maxAgeDays * 86400;
    this.document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax${secure}`;
  }

  delete(name: string): void {
    this.set(name, '', 0);
  }
}
