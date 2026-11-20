import { HttpClient } from '@angular/common/http';
import { HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ME, testProviders } from '../../testing';
import { authGuard, guestGuard, safeReturnUrl } from './auth.guards';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let auth: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: testProviders() });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('resolves the session once from /me', async () => {
    const first = auth.ensureLoaded();
    const second = auth.ensureLoaded();
    http.expectOne('/api/v1/auth/me').flush(ME);
    await Promise.all([first, second]);
    expect(auth.status()).toBe('authenticated');
    expect(auth.user()?.profile.nickname).toBe('ana-dev');
  });

  it('is anonymous when /me answers 401', async () => {
    const loading = auth.ensureLoaded();
    http
      .expectOne('/api/v1/auth/me')
      .flush({ error: { code: 'not_authenticated' } }, { status: 401, statusText: 'Unauthorized' });
    await loading;
    expect(auth.status()).toBe('anonymous');
  });

  it('login stores the user', async () => {
    const result = firstValueFrom(
      auth.login({ email: 'ana@example.com', password: 'x'.repeat(12), remember_me: true }),
    );
    const req = http.expectOne('/api/v1/auth/login');
    expect(req.request.body.remember_me).toBe(true);
    req.flush(ME);
    await result;
    expect(auth.status()).toBe('authenticated');
  });

  it('logout ends the local session even if the request fails', async () => {
    const done = firstValueFrom(auth.logout()).catch(() => undefined);
    http.expectOne('/api/v1/auth/logout').flush(null, { status: 401, statusText: 'Unauthorized' });
    await done;
    expect(auth.status()).toBe('anonymous');
  });
});

describe('auth interceptors', () => {
  let http: HttpTestingController;
  let client: HttpClient;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: testProviders() });
    http = TestBed.inject(HttpTestingController);
    client = TestBed.inject(HttpClient);
    document.cookie = 'pp_csrf=token-123; path=/';
  });

  afterEach(() => {
    document.cookie = 'pp_csrf=; path=/; max-age=0';
    http.verify();
  });

  it('adds X-CSRF-Token to unsafe API requests only', () => {
    client.post('/api/v1/auth/logout', null).subscribe();
    client.get('/api/v1/auth/me').subscribe();
    client.post('https://external.example/x', null).subscribe();

    expect(http.expectOne('/api/v1/auth/logout').request.headers.get('X-CSRF-Token')).toBe(
      'token-123',
    );
    expect(http.expectOne('/api/v1/auth/me').request.headers.has('X-CSRF-Token')).toBe(false);
    expect(
      http.expectOne('https://external.example/x').request.headers.has('X-CSRF-Token'),
    ).toBe(false);
  });

  it('marks the session anonymous on any API 401', () => {
    const auth = TestBed.inject(AuthService);
    client.get('/api/v1/anything').subscribe({ error: () => undefined });
    http.expectOne('/api/v1/anything').flush(null, { status: 401, statusText: 'Unauthorized' });
    expect(auth.status()).toBe('anonymous');
  });
});

describe('guards', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: testProviders() });
    http = TestBed.inject(HttpTestingController);
  });

  function runGuard(guard: typeof guestGuard, url = '/x') {
    return TestBed.runInInjectionContext(() =>
      guard({} as never, { url } as never),
    ) as Promise<boolean | UrlTree>;
  }

  it('guestGuard redirects authenticated users home', async () => {
    const result = runGuard(guestGuard);
    http.expectOne('/api/v1/auth/me').flush(ME);
    const tree = (await result) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(tree)).toBe('/');
  });

  it('guestGuard lets visitors through', async () => {
    const result = runGuard(guestGuard);
    http.expectOne('/api/v1/auth/me').flush(null, { status: 401, statusText: 'Unauthorized' });
    expect(await result).toBe(true);
  });

  it('authGuard sends visitors to login with returnUrl', async () => {
    const result = runGuard(authGuard, '/settings');
    http.expectOne('/api/v1/auth/me').flush(null, { status: 401, statusText: 'Unauthorized' });
    const tree = (await result) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(tree)).toBe('/login?returnUrl=%2Fsettings');
  });

  it.each([
    ['/settings', '/settings'],
    ['//evil.example', '/'],
    ['https://evil.example', '/'],
    ['/\\evil.example', '/'],
    [null, '/'],
  ])('safeReturnUrl(%s) = %s', (input, expected) => {
    expect(safeReturnUrl(input)).toBe(expected);
  });
});
