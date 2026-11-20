import { Component, DestroyRef, ElementRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { RegisterPayload } from '../../core/auth/auth.models';
import { AuthService } from '../../core/auth/auth.service';
import { generalErrorKey, parseApiError } from '../../core/http/api-error';
import { LANGUAGES, LanguageService } from '../../core/i18n/language.service';
import { FieldError } from '../../shared/field-error/field-error';
import { focusFirstInvalid } from '../../shared/forms';
import {
  MIN_REGISTRATION_AGE,
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  birthDate,
  matches,
  nicknameAvailable,
  nicknameFormat,
  normalizeNickname,
} from './validators';

const CODE_TO_FIELD: Record<string, [string, string]> = {
  email_taken: ['email', 'emailTaken'],
  nickname_taken: ['nickname', 'nicknameTaken'],
};

@Component({
  selector: 'app-register-page',
  imports: [ReactiveFormsModule, RouterLink, TranslatePipe, FieldError],
  templateUrl: './register.page.html',
})
export class RegisterPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  protected readonly languages = LANGUAGES;
  protected readonly languageNames = { es: 'Español', en: 'English' };
  protected readonly passwordMin = PASSWORD_MIN_LENGTH;

  private readonly fb = inject(NonNullableFormBuilder);
  protected readonly form = this.fb.group({
    first_name: ['', [Validators.required, Validators.maxLength(100)]],
    last_name: ['', [Validators.required, Validators.maxLength(100)]],
    nickname: this.fb.control('', {
      validators: [Validators.required, nicknameFormat],
      asyncValidators: [nicknameAvailable((n) => this.auth.checkNickname(n))],
      // Una sola comprobación al salir del campo, no una petición por pulsación.
      updateOn: 'blur',
    }),
    birth_date: ['', [Validators.required, birthDate(MIN_REGISTRATION_AGE)]],
    location: ['', [Validators.required, Validators.maxLength(120)]],
    job_title: ['', [Validators.required, Validators.maxLength(120)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(254)]],
    password: [
      '',
      [
        Validators.required,
        Validators.minLength(PASSWORD_MIN_LENGTH),
        Validators.maxLength(PASSWORD_MAX_LENGTH),
      ],
    ],
    password_confirm: ['', [Validators.required, matches('password')]],
    visibility: this.fb.control<'public' | 'private'>('public'),
    preferred_language: this.fb.control(inject(LanguageService).current()),
  });

  protected readonly submitting = signal(false);
  protected readonly errorKey = signal<string | null>(null);
  private readonly nicknameState = signal({ status: 'VALID', value: '' });
  protected readonly nicknamePreview = computed(() => normalizeNickname(this.nicknameState().value));
  protected readonly nicknameChecking = computed(() => this.nicknameState().status === 'PENDING');
  protected readonly nicknameAvailable = computed(
    () => this.nicknameState().status === 'VALID' && this.nicknamePreview() !== '',
  );

  constructor() {
    const destroyRef = inject(DestroyRef);
    const { nickname, password, password_confirm } = this.form.controls;
    nickname.events.pipe(takeUntilDestroyed(destroyRef)).subscribe(() =>
      this.nicknameState.set({ status: nickname.status, value: nickname.value }),
    );
    password.valueChanges
      .pipe(takeUntilDestroyed(destroyRef))
      .subscribe(() => password_confirm.updateValueAndValidity({ emitEvent: false }));
  }

  protected submit(): void {
    this.errorKey.set(null);
    if (this.form.invalid || this.form.pending) {
      this.form.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    const value = this.form.getRawValue();
    const payload: RegisterPayload = { ...value, nickname: normalizeNickname(value.nickname) };
    this.submitting.set(true);
    this.auth.register(payload).subscribe({
      next: () => void this.router.navigateByUrl('/'),
      error: (error: unknown) => {
        this.submitting.set(false);
        this.showServerErrors(error);
      },
    });
  }

  private showServerErrors(error: unknown): void {
    const info = parseApiError(error);
    const conflict = info.code ? CODE_TO_FIELD[info.code] : undefined;
    const fields = conflict ? [conflict] : info.fields.map((f): [string, string] => [f, 'server']);
    const controls = fields
      .map(([name, key]) => ({ control: this.form.get(name), key }))
      .filter((item) => item.control !== null);
    if (controls.length === 0) {
      this.errorKey.set(generalErrorKey(info));
      return;
    }
    for (const { control, key } of controls) {
      control?.setErrors({ [key]: true });
      control?.markAsTouched();
    }
    focusFirstInvalid(this.host.nativeElement);
  }
}
