import { Language } from '../i18n/language.service';

/** Contratos de docs/API_SPECIFICATION.md (Auth). */
export type ProfileVisibility = 'public' | 'private';

export interface ProfileSummary {
  nickname: string;
  display_name: string;
  first_name: string;
  last_name: string;
  visibility: ProfileVisibility;
  preferred_language: Language;
}

export interface Me {
  id: string;
  email: string;
  role: 'user' | 'admin';
  profile: ProfileSummary;
}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me: boolean;
}

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  nickname: string;
  birth_date: string;
  location: string;
  job_title: string;
  email: string;
  password: string;
  password_confirm: string;
  visibility: ProfileVisibility;
  preferred_language: Language;
}

export interface NicknameAvailability {
  nickname: string;
  available: boolean;
  reason: 'invalid' | 'reserved' | 'taken' | null;
}

/** 'unknown' = aún sin consultar (siempre en SSR: la sesión se resuelve en el navegador). */
export type AuthState =
  | { status: 'unknown' }
  | { status: 'anonymous' }
  | { status: 'authenticated'; user: Me };
