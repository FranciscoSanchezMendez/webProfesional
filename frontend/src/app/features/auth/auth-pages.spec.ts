import { HttpTestingController } from '@angular/common/http/testing';
import { Type } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { ME, testProviders } from '../../testing';
import { LoginPage } from './login.page';
import { RegisterPage } from './register.page';

async function setup<T>(component: Type<T>) {
  TestBed.configureTestingModule({ imports: [component], providers: testProviders() });
  await firstValueFrom(TestBed.inject(TranslateService).use('es'));
  const fixture = TestBed.createComponent(component);
  await fixture.whenStable();
  const el = fixture.nativeElement as HTMLElement;
  const http = TestBed.inject(HttpTestingController);
  const type = (selector: string, value: string) => {
    const input = el.querySelector<HTMLInputElement>(selector)!;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new Event('blur'));
  };
  const submit = async () => {
    el.querySelector<HTMLButtonElement>('button[type=submit]')!.click();
    await fixture.whenStable();
  };
  return { fixture, el, http, type, submit };
}

describe('LoginPage', () => {
  it('shows field errors and sends nothing when the form is empty', async () => {
    const { el, http, submit } = await setup(LoginPage);
    await submit();
    expect(el.querySelectorAll('.field-error').length).toBe(2);
    http.expectNone('/api/v1/auth/login');
  });

  it('shows a generic message on invalid credentials', async () => {
    const { el, http, type, submit, fixture } = await setup(LoginPage);
    type('#login-email', 'ana@example.com');
    type('#login-password', 'incorrecta-123');
    await submit();
    http
      .expectOne('/api/v1/auth/login')
      .flush(
        { error: { code: 'invalid_credentials', message: '' } },
        { status: 401, statusText: 'Unauthorized' },
      );
    await fixture.whenStable();
    expect(el.querySelector('[data-testid=form-error]')?.textContent).toContain(
      'Email o contraseña incorrectos.',
    );
  });

  it('navigates home after logging in', async () => {
    const { http, type, submit, fixture } = await setup(LoginPage);
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    type('#login-email', 'ana@example.com');
    type('#login-password', 'una-contraseña-larga');
    await submit();
    http.expectOne('/api/v1/auth/login').flush(ME);
    await fixture.whenStable();
    expect(navigate).toHaveBeenCalledWith('/');
    expect(TestBed.inject(AuthService).status()).toBe('authenticated');
  });
});

describe('RegisterPage', () => {
  it('checks the nickname only when leaving the field', async () => {
    const { el, http, fixture } = await setup(RegisterPage);
    const input = el.querySelector<HTMLInputElement>('#reg-nickname')!;
    for (const value of ['a', 'an', 'ana']) {
      input.value = value;
      input.dispatchEvent(new Event('input'));
    }
    http.expectNone((req) => req.url.endsWith('/nickname-availability'));
    input.dispatchEvent(new Event('blur'));
    const req = http.expectOne((r) => r.url.endsWith('/nickname-availability'));
    expect(req.request.params.get('nickname')).toBe('ana');
    req.flush({ nickname: 'ana', available: false, reason: 'taken' });
    await fixture.whenStable();
    expect(el.textContent).toContain('Este nickname ya está en uso.');
  });

  it('maps a 409 email_taken to the email field', async () => {
    const { el, http, type, submit, fixture } = await setup(RegisterPage);
    type('#reg-first-name', 'Ana');
    type('#reg-last-name', 'García');
    type('#reg-nickname', '@Ana-Dev');
    http
      .expectOne((r) => r.url.endsWith('/nickname-availability'))
      .flush({ nickname: 'ana-dev', available: true, reason: null });
    type('#reg-birth-date', '1990-05-17');
    type('#reg-location', 'Sevilla');
    type('#reg-job-title', 'Dev');
    type('#reg-email', 'ana@example.com');
    type('#reg-password', 'una-contraseña-larga');
    type('#reg-password-confirm', 'una-contraseña-larga');
    await submit();

    const req = http.expectOne('/api/v1/auth/register');
    expect(req.request.body.nickname).toBe('ana-dev');
    req.flush(
      { error: { code: 'email_taken', message: '' } },
      { status: 409, statusText: 'Conflict' },
    );
    await fixture.whenStable();
    expect(el.querySelector('#reg-email-error')?.textContent).toContain(
      'Ya existe una cuenta con este email.',
    );
  });
});
