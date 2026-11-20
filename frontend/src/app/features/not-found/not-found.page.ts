import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

/** En SSR responde con estado 404 (ver app.routes.server.ts). */
@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink, TranslatePipe],
  template: `
    <section class="page">
      <h1>{{ 'notFound.title' | translate }}</h1>
      <p>{{ 'notFound.body' | translate }}</p>
      <a class="btn btn-primary" routerLink="/">{{ 'notFound.home' | translate }}</a>
    </section>
  `,
})
export class NotFoundPage {}
