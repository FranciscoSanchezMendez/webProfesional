import { HttpTestingController } from '@angular/common/http/testing';
import { Type } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { TranslateService } from '@ngx-translate/core';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../core/auth/auth.service';
import { LanguageService } from '../core/i18n/language.service';
import { ThemeService } from '../core/theme/theme.service';
import { ME, testProviders } from '../testing';
import { Footer } from './footer/footer';
import { Header } from './header/header';

async function render<T>(component: Type<T>) {
  TestBed.configureTestingModule({ imports: [component], providers: testProviders() });
  await firstValueFrom(TestBed.inject(TranslateService).use('es'));
  const fixture = TestBed.createComponent(component);
  await fixture.whenStable();
  return { fixture, el: fixture.nativeElement as HTMLElement };
}

describe('Header', () => {
  it('reserves space while the session is unknown (SSR)', async () => {
    const { el } = await render(Header);
    expect(el.querySelector('.site-header__placeholder')).not.toBeNull();
    expect(el.textContent).not.toContain('Iniciar sesión');
  });

  it('shows login and register to visitors', async () => {
    const { el, fixture } = await render(Header);
    TestBed.inject(AuthService).markAnonymous();
    await fixture.whenStable();
    expect(el.textContent).toContain('Iniciar sesión');
    expect(el.textContent).toContain('Crear cuenta');
  });

  it('shows avatar initials and name for a signed-in user', async () => {
    const { el, fixture } = await render(Header);
    const loading = TestBed.inject(AuthService).ensureLoaded();
    TestBed.inject(HttpTestingController).expectOne('/api/v1/auth/me').flush(ME);
    await loading;
    await fixture.whenStable();
    expect(el.querySelector('.avatar')?.textContent?.trim()).toBe('AG');
    expect(el.textContent).toContain('Ana García');
    expect(el.textContent).toContain('@ana-dev');
  });
});

describe('Footer preferences', () => {
  afterEach(() => {
    document.cookie = 'pp_lang=; path=/; max-age=0';
    document.cookie = 'pp_theme=; path=/; max-age=0';
    document.documentElement.removeAttribute('data-theme');
  });

  it('changes and remembers the language', async () => {
    const { el, fixture } = await render(Footer);
    const select = el.querySelector<HTMLSelectElement>('[data-testid=language-select]')!;
    select.value = 'en';
    select.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    expect(TestBed.inject(LanguageService).current()).toBe('en');
    expect(document.documentElement.lang).toBe('en');
    expect(document.cookie).toContain('pp_lang=en');
    // Las traducciones en inglés se cargan con import() dinámico.
    await vi.waitFor(async () => {
      await fixture.whenStable();
      expect(el.textContent).toContain('About');
    });
  });

  it('changes and remembers the theme; system removes the override', async () => {
    const { el, fixture } = await render(Footer);
    const select = el.querySelector<HTMLSelectElement>('[data-testid=theme-select]')!;
    select.value = 'dark';
    select.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    expect(document.documentElement.dataset['theme']).toBe('dark');
    expect(document.cookie).toContain('pp_theme=dark');

    TestBed.inject(ThemeService).use('system');
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
    expect(document.cookie).not.toContain('pp_theme=dark');
  });
});
