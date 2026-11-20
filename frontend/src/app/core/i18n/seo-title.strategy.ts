import { Injectable, inject } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';

/**
 * El `title` de cada ruta es una clave de traducción. También aplica `data.robots`
 * (p. ej. 'noindex' en login/registro/404) y se actualiza al cambiar de idioma.
 */
@Injectable({ providedIn: 'root' })
export class SeoTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly meta = inject(Meta);
  private readonly translate = inject(TranslateService);
  private last: RouterStateSnapshot | null = null;

  constructor() {
    super();
    this.translate.onLangChange.subscribe(() => this.last && this.updateTitle(this.last));
  }

  override updateTitle(snapshot: RouterStateSnapshot): void {
    this.last = snapshot;
    const key = this.buildTitle(snapshot);
    const appName = this.translate.instant('app.name') as string;
    const page = key ? (this.translate.instant(key) as string) : appName;
    this.title.setTitle(page === appName ? appName : `${page} · ${appName}`);

    let route = snapshot.root;
    while (route.firstChild) {
      route = route.firstChild;
    }
    const robots: unknown = route.data['robots'];
    if (typeof robots === 'string') {
      this.meta.updateTag({ name: 'robots', content: robots });
    } else {
      this.meta.removeTag('name="robots"');
    }
  }
}
