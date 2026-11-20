/** Lleva el foco al primer campo inválido (accesibilidad tras un envío fallido). */
export function focusFirstInvalid(root: HTMLElement): void {
  root.querySelector<HTMLElement>('input.ng-invalid, select.ng-invalid, textarea.ng-invalid')?.focus();
}
