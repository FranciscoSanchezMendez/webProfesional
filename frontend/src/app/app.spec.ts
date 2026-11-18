import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { App } from './app';

describe('App', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  async function render(): Promise<HTMLElement> {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('renders the brand title', async () => {
    const el = await render();
    httpMock.match('/api/v1/health/ready');
    expect(el.querySelector('h1')?.textContent).toContain('PersonalProfile');
  });

  it('shows ok when the API is ready', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    httpMock.expectOne('/api/v1/health/ready').flush({ status: 'ok', database: 'ok' });
    await fixture.whenStable();
    const status = (fixture.nativeElement as HTMLElement).querySelector('[data-testid=api-status]');
    expect(status?.getAttribute('data-state')).toBe('ok');
  });

  it('shows degraded when the database is unavailable', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    httpMock
      .expectOne('/api/v1/health/ready')
      .flush({ status: 'error', database: 'unavailable' }, { status: 503, statusText: 'Service Unavailable' });
    await fixture.whenStable();
    const status = (fixture.nativeElement as HTMLElement).querySelector('[data-testid=api-status]');
    expect(status?.getAttribute('data-state')).toBe('degraded');
  });
});
