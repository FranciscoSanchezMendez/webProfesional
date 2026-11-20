import { FormControl, FormGroup } from '@angular/forms';
import { firstValueFrom, of, throwError } from 'rxjs';

import {
  ageOn,
  birthDate,
  matches,
  nicknameAvailable,
  nicknameFormat,
  normalizeNickname,
} from './validators';

describe('register validators', () => {
  it('normalizes nicknames like the backend', () => {
    expect(normalizeNickname('  @Ana-Dev ')).toBe('ana-dev');
  });

  it.each(['ana', 'a-b', '@Ana-Dev', 'x'.repeat(30)])('accepts nickname %s', (value) => {
    expect(nicknameFormat(new FormControl(value))).toBeNull();
  });

  it.each(['ab', '-ana', 'ana-', 'a_b', 'ñandú', 'x'.repeat(31)])('rejects nickname %s', (value) => {
    expect(nicknameFormat(new FormControl(value))).toEqual({ nicknameFormat: true });
  });

  it('maps availability answers to errors and ignores network failures', async () => {
    const answer = (reason: 'taken' | 'reserved' | null) =>
      nicknameAvailable(() => of({ nickname: 'x', available: reason === null, reason }));
    const control = new FormControl('ana');
    await expect(firstValueFrom(answer(null)(control) as never)).resolves.toBeNull();
    await expect(firstValueFrom(answer('taken')(control) as never)).resolves.toEqual({
      nicknameTaken: true,
    });
    await expect(firstValueFrom(answer('reserved')(control) as never)).resolves.toEqual({
      nicknameReserved: true,
    });
    const failing = nicknameAvailable(() => throwError(() => new Error('offline')));
    await expect(firstValueFrom(failing(control) as never)).resolves.toBeNull();
  });

  it('computes age around birthdays', () => {
    expect(ageOn(new Date(2010, 5, 15), new Date(2024, 5, 14))).toBe(13);
    expect(ageOn(new Date(2010, 5, 15), new Date(2024, 5, 15))).toBe(14);
  });

  it('requires a past date and a minimum age', () => {
    const today = () => new Date(2026, 10, 18);
    const validator = birthDate(14, today);
    expect(validator(new FormControl('2012-11-18'))).toBeNull();
    expect(validator(new FormControl('2012-11-19'))).toEqual({ minAge: { age: 14 } });
    expect(validator(new FormControl('2026-11-18'))).toEqual({ futureDate: true });
    expect(validator(new FormControl(''))).toBeNull();
  });

  it('checks that the confirmation matches', () => {
    const group = new FormGroup({
      password: new FormControl('una-contraseña-larga'),
      confirm: new FormControl('otra', [matches('password')]),
    });
    // Al construir el grupo el control aún no tiene padre: en el formulario se revalida al escribir.
    group.controls.confirm.updateValueAndValidity();
    expect(group.controls.confirm.errors).toEqual({ passwordMismatch: true });
    group.controls.confirm.setValue('una-contraseña-larga');
    expect(group.controls.confirm.errors).toBeNull();
  });
});
