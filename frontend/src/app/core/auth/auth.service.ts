import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { Observable, finalize, firstValueFrom, map, tap } from 'rxjs';

import { LanguageService } from '../i18n/language.service';
import {
  AuthState,
  LoginPayload,
  Me,
  NicknameAvailability,
  RegisterPayload,
} from './auth.models';

export const AUTH_API = '/api/v1/auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly language = inject(LanguageService);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  private readonly state = signal<AuthState>({ status: 'unknown' });
  private loading: Promise<void> | null = null;

  readonly status = computed(() => this.state().status);
  readonly user = computed(() => {
    const state = this.state();
    return state.status === 'authenticated' ? state.user : null;
  });

  /**
   * Consulta /me una sola vez. En SSR no se hace: la cookie de sesión no se reenvía al
   * backend en esta fase y el HTML no debe depender del usuario (D-019).
   */
  ensureLoaded(): Promise<void> {
    if (!this.isBrowser || this.state().status !== 'unknown') {
      return Promise.resolve();
    }
    this.loading ??= firstValueFrom(this.http.get<Me>(`${AUTH_API}/me`))
      .then((user) => this.state.set({ status: 'authenticated', user }))
      .catch(() => this.state.set({ status: 'anonymous' }))
      .finally(() => (this.loading = null));
    return this.loading;
  }

  login(payload: LoginPayload): Observable<Me> {
    return this.http.post<Me>(`${AUTH_API}/login`, payload).pipe(tap((user) => this.signIn(user)));
  }

  register(payload: RegisterPayload): Observable<Me> {
    return this.http
      .post<Me>(`${AUTH_API}/register`, payload)
      .pipe(tap((user) => this.signIn(user)));
  }

  logout(): Observable<void> {
    return this.http.post<void>(`${AUTH_API}/logout`, null).pipe(
      map(() => undefined),
      // Aunque falle (p. ej. sesión ya caducada), localmente la sesión termina.
      finalize(() => this.markAnonymous()),
    );
  }

  checkNickname(nickname: string): Observable<NicknameAvailability> {
    return this.http.get<NicknameAvailability>(`${AUTH_API}/nickname-availability`, {
      params: { nickname },
    });
  }

  markAnonymous(): void {
    this.state.set({ status: 'anonymous' });
  }

  private signIn(user: Me): void {
    this.state.set({ status: 'authenticated', user });
    // Al entrar se aplica el idioma preferido de la cuenta.
    this.language.use(user.profile.preferred_language).subscribe();
  }
}
