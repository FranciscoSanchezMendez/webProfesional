import { HttpErrorResponse } from '@angular/common/http';

/** Errores de la API (docs/API_SPECIFICATION.md, Convenciones). */
export interface ApiErrorInfo {
  status: number;
  /** `error.code` de los errores de negocio (p. ej. 'email_taken'). */
  code: string | null;
  /** Campos con error de validación 422 (loc ["body", campo]). */
  fields: string[];
}

interface ValidationItem {
  loc?: (string | number)[];
}

export function parseApiError(error: unknown): ApiErrorInfo {
  if (!(error instanceof HttpErrorResponse)) {
    return { status: -1, code: null, fields: [] };
  }
  const body: unknown = error.error;
  let code: string | null = null;
  let fields: string[] = [];
  if (body && typeof body === 'object') {
    const apiError = (body as { error?: { code?: unknown } }).error;
    if (apiError && typeof apiError.code === 'string') {
      code = apiError.code;
    }
    const detail = (body as { detail?: unknown }).detail;
    if (Array.isArray(detail)) {
      fields = (detail as ValidationItem[])
        .map((item) => item.loc?.[1])
        .filter((field): field is string => typeof field === 'string');
    }
  }
  return { status: error.status, code, fields };
}

/** Clave de traducción para un error que no corresponde a un campo concreto. */
export function generalErrorKey(info: ApiErrorInfo): string {
  if (info.status === 0) {
    return 'errors.network';
  }
  switch (info.code) {
    case 'invalid_credentials':
      return 'errors.invalidCredentials';
    case 'rate_limited':
      return 'errors.rateLimited';
    default:
      return 'errors.unexpected';
  }
}
