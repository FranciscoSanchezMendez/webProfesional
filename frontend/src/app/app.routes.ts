import { Routes } from '@angular/router';

import { guestGuard } from './core/auth/auth.guards';
import { HomePage } from './features/home/home.page';

/** `title` es una clave de traducción (SeoTitleStrategy). `data.robots` añade la meta robots. */
export const routes: Routes = [
  { path: '', component: HomePage, title: 'titles.home' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login.page').then((m) => m.LoginPage),
    canActivate: [guestGuard],
    title: 'titles.login',
    data: { robots: 'noindex' },
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register.page').then((m) => m.RegisterPage),
    canActivate: [guestGuard],
    title: 'titles.register',
    data: { robots: 'noindex' },
  },
  ...(
    [
      ['about', 'info.aboutTitle', 'titles.about'],
      ['contact', 'info.contactTitle', 'titles.contact'],
      ['faq', 'info.faqTitle', 'titles.faq'],
    ] as const
  ).map(([path, heading, title]) => ({
    path,
    loadComponent: () => import('./features/info/info.page').then((m) => m.InfoPage),
    title,
    data: { heading },
  })),
  {
    path: '**',
    loadComponent: () =>
      import('./features/not-found/not-found.page').then((m) => m.NotFoundPage),
    title: 'titles.notFound',
    data: { robots: 'noindex' },
  },
];
