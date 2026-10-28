import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { ApplicationConfig } from '@angular/core';
import { provideRouter, withInMemoryScrolling } from '@angular/router';
import Aura from '@primeuix/themes/aura';
import { providePrimeNG } from 'primeng/config';
import { appRoutes } from './app.routes';
import { apiErrorInterceptor } from './core/interceptors/api-error.interceptor';
import { WORK_ITEM_STORE } from './features/work-items/data-access/work-item-store';
import { InMemoryWorkItemStore } from './features/work-items/data-access/in-memory-work-item.store';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      appRoutes,
      withInMemoryScrolling({ scrollPositionRestoration: 'enabled' }),
    ),
    provideHttpClient(withInterceptors([apiErrorInterceptor])),
    provideAnimationsAsync(),
    providePrimeNG({
      theme: {
        preset: Aura,
        options: {
          // Keep the dashboard light even when the operating system uses dark mode.
          darkModeSelector: '.app-dark',
          cssLayer: false,
        },
      },
      ripple: true,
    }),
    // Demo adapter only. Replace this provider with an Azure DevOps API-backed store.
    { provide: WORK_ITEM_STORE, useClass: InMemoryWorkItemStore },
  ],
};
