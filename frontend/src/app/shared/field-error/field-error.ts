import { Component, computed, effect, input, signal } from '@angular/core';
import { AbstractControl } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';

/** Validadores → clave de traducción. El orden define qué mensaje se muestra primero. */
const MESSAGES: Record<string, string> = {
  required: 'errors.required',
  email: 'errors.email',
  minlength: 'errors.minlength',
  maxlength: 'errors.maxlength',
  nicknameFormat: 'errors.nicknameFormat',
  nicknameReserved: 'errors.nicknameReserved',
  nicknameTaken: 'errors.nicknameTaken',
  emailTaken: 'errors.emailTaken',
  futureDate: 'errors.futureDate',
  minAge: 'errors.minAge',
  passwordMismatch: 'errors.passwordMismatch',
  server: 'errors.invalid',
};

/**
 * Mensaje breve bajo un campo, visible tras tocarlo. El input lo enlaza con
 * aria-describedby usando `errorId` para que lo anuncien los lectores de pantalla.
 */
@Component({
  selector: 'app-field-error',
  imports: [TranslatePipe],
  template: `
    @if (message(); as m) {
      <p class="field-error" [id]="errorId()">{{ m.key | translate: m.params }}</p>
    }
  `,
})
export class FieldError {
  readonly control = input.required<AbstractControl>();
  readonly errorId = input.required<string>();

  /** Se incrementa con cada evento del control (valor, estado, touched…), incluida la validación asíncrona. */
  private readonly version = signal(0);

  protected readonly message = computed(() => {
    this.version();
    const control = this.control();
    if (!control.errors || !(control.touched || control.dirty)) {
      return null;
    }
    const name = Object.keys(MESSAGES).find((key) => control.errors?.[key]);
    const detail: unknown = name ? control.errors[name] : null;
    return {
      key: name ? MESSAGES[name] : 'errors.invalid',
      params: typeof detail === 'object' && detail !== null ? detail : {},
    };
  });

  constructor() {
    effect((onCleanup) => {
      const sub = this.control().events.subscribe(() => this.version.update((v) => v + 1));
      onCleanup(() => sub.unsubscribe());
    });
  }
}
