import { Component, ElementRef, computed, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly menu = viewChild<ElementRef<HTMLElement>>('menu');

  protected readonly initials = computed(() => {
    const profile = this.auth.user()?.profile;
    if (!profile) {
      return '';
    }
    return `${profile.first_name.charAt(0)}${profile.last_name.charAt(0)}`.toUpperCase();
  });

  protected logout(): void {
    this.menu()?.nativeElement.hidePopover?.();
    this.auth.logout().subscribe({
      complete: () => void this.router.navigateByUrl('/'),
      error: () => void this.router.navigateByUrl('/'),
    });
  }
}
