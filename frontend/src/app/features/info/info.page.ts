import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { map } from 'rxjs';

/** About / Contact / FAQ. El contenido real se redactará más adelante (Fase 9: legal y SEO). */
@Component({
  selector: 'app-info-page',
  imports: [TranslatePipe],
  template: `
    <section class="page">
      <h1>{{ heading() | translate }}</h1>
      <p class="muted">{{ 'info.placeholder' | translate }}</p>
    </section>
  `,
})
export class InfoPage {
  protected readonly heading = toSignal(
    inject(ActivatedRoute).data.pipe(map((data) => data['heading'] as string)),
    { initialValue: '' },
  );
}
