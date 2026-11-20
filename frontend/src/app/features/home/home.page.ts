import { Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

import { AuthService } from '../../core/auth/auth.service';

/** Marcador de la home: en Fase 4 mostrará el perfil del creador. */
@Component({
  selector: 'app-home-page',
  imports: [TranslatePipe],
  template: `
    <section class="page">
      <h1>{{ 'home.title' | translate }}</h1>
      <p class="lead">{{ 'home.lead' | translate }}</p>
      @if (auth.user(); as user) {
        <p data-testid="welcome">
          {{ 'home.welcome' | translate: { name: user.profile.display_name } }}
        </p>
      }
      <p class="muted">{{ 'home.soon' | translate }}</p>
    </section>
  `,
})
export class HomePage {
  protected readonly auth = inject(AuthService);
}
