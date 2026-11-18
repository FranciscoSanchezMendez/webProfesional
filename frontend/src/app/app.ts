import { HttpErrorResponse } from '@angular/common/http';
import { Component, afterNextRender, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { HealthService } from './core/health/health.service';

type ApiState = 'checking' | 'ok' | 'degraded' | 'down';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly health = inject(HealthService);
  protected readonly apiState = signal<ApiState>('checking');

  constructor() {
    // El estado técnico no es contenido indexable: se consulta solo en el navegador.
    afterNextRender(() => this.checkApi());
  }

  private checkApi(): void {
    this.health.readiness().subscribe({
      next: () => this.apiState.set('ok'),
      error: (err: HttpErrorResponse) => this.apiState.set(err.status === 503 ? 'degraded' : 'down'),
    });
  }
}
