import { AbstractControl, AsyncValidatorFn, ValidationErrors, ValidatorFn } from '@angular/forms';
import { Observable, catchError, map, of } from 'rxjs';

import { NicknameAvailability } from '../../core/auth/auth.models';

/**
 * Reglas espejo del backend (docs/API_SPECIFICATION.md). Son solo para dar feedback inmediato:
 * la validación definitiva siempre la repite la API.
 */
/** Deben coincidir con backend/app/schemas/auth.py (D-022). */
export const PASSWORD_MIN_LENGTH = 7;
export const PASSWORD_MAX_LENGTH = 30;
/** Debe coincidir con MIN_REGISTRATION_AGE del backend (D-014). */
export const MIN_REGISTRATION_AGE = 14;
const NICKNAME_RE = /^[a-z0-9]([a-z0-9-]{1,28})[a-z0-9]$/;

export function normalizeNickname(value: string): string {
  return value.trim().replace(/^@/, '').toLowerCase();
}

export const nicknameFormat: ValidatorFn = (control) => {
  const value = typeof control.value === 'string' ? normalizeNickname(control.value) : '';
  return !value || NICKNAME_RE.test(value) ? null : { nicknameFormat: true };
};

/** Consulta de disponibilidad. Se usa con updateOn: 'blur' (una petición al salir del campo). */
export function nicknameAvailable(
  check: (nickname: string) => Observable<NicknameAvailability>,
): AsyncValidatorFn {
  return (control: AbstractControl): Observable<ValidationErrors | null> => {
    const value = normalizeNickname(String(control.value ?? ''));
    if (!value) {
      return of(null);
    }
    return check(value).pipe(
      map((result) => {
        switch (result.reason) {
          case null:
            return null;
          case 'taken':
            return { nicknameTaken: true };
          case 'reserved':
            return { nicknameReserved: true };
          default:
            return { nicknameFormat: true };
        }
      }),
      // Si la comprobación falla (red, 429) no se bloquea el formulario: decide el registro.
      catchError(() => of(null)),
    );
  };
}

export function ageOn(birth: Date, today: Date): number {
  const beforeBirthday =
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate());
  return today.getFullYear() - birth.getFullYear() - (beforeBirthday ? 1 : 0);
}

/** Valor de <input type="date"> (AAAA-MM-DD) interpretado como fecha local, sin zona horaria. */
function parseDateInput(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return match ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])) : null;
}

export function birthDate(minAge: number, today: () => Date = () => new Date()): ValidatorFn {
  return (control) => {
    const date = typeof control.value === 'string' ? parseDateInput(control.value) : null;
    if (!date) {
      return null; // 'required' cubre el vacío
    }
    const now = today();
    if (date >= new Date(now.getFullYear(), now.getMonth(), now.getDate())) {
      return { futureDate: true };
    }
    return ageOn(date, now) < minAge ? { minAge: { age: minAge } } : null;
  };
}

/** Se aplica al campo de confirmación; se revalida cuando cambia la contraseña. */
export function matches(otherName: string): ValidatorFn {
  return (control) => {
    const other = control.parent?.get(otherName);
    if (!other || !control.value) {
      return null;
    }
    return control.value === other.value ? null : { passwordMismatch: true };
  };
}
