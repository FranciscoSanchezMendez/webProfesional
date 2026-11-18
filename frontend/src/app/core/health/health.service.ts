import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface ReadinessResponse {
  status: 'ok' | 'error';
  database: 'ok' | 'unavailable';
}

@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);

  /** Ruta relativa: el navegador habla con el mismo origen y el proxy la reenvía a FastAPI. */
  readiness(): Observable<ReadinessResponse> {
    return this.http.get<ReadinessResponse>('/api/v1/health/ready');
  }
}
