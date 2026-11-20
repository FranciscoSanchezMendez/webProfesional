import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { LANGUAGES, LanguageService, isLanguage } from '../../core/i18n/language.service';
import { THEMES, Theme, ThemeService } from '../../core/theme/theme.service';

const THEME_KEYS: Record<Theme, string> = {
  system: 'footer.themeSystem',
  light: 'footer.themeLight',
  dark: 'footer.themeDark',
};

@Component({
  selector: 'app-footer',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './footer.html',
  styleUrl: './footer.scss',
})
export class Footer {
  protected readonly language = inject(LanguageService);
  protected readonly theme = inject(ThemeService);
  protected readonly languages = LANGUAGES;
  protected readonly themes = THEMES;
  protected readonly themeKeys = THEME_KEYS;
  /** Nombre de cada idioma en su propio idioma (no se traduce). */
  protected readonly languageNames = { es: 'Español', en: 'English' };
  protected readonly year = new Date().getFullYear();

  protected changeLanguage(value: string): void {
    if (isLanguage(value)) {
      this.language.use(value).subscribe();
    }
  }

  protected changeTheme(value: string): void {
    if ((THEMES as readonly string[]).includes(value)) {
      this.theme.use(value as Theme);
    }
  }
}
