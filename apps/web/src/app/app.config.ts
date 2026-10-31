import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withInMemoryScrolling } from '@angular/router';

import Aura from '@primeuix/themes/aura';
import { providePrimeNG } from 'primeng/config';

import { appRoutes } from './app.routes';
import { apiErrorInterceptor } from './core/interceptors/api-error.interceptor';

import { WORK_ITEM_STORE } from './features/work-items/data-access/work-item-store';
import { AzureDevOpsWorkItemStore } from './features/work-items/data-access/azure-devops-work-item.store';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      appRoutes,
      withInMemoryScrolling({
        scrollPositionRestoration: 'enabled',
      }),
    ),

    provideHttpClient(
      withInterceptors([apiErrorInterceptor]),
    ),

    provideAnimationsAsync(),

    providePrimeNG({
      theme: {
        preset: Aura,
        options: {
          darkModeSelector: '.app-dark',
          cssLayer: false,
        },
      },
      ripple: true,
    }),

    // Production data source: Azure DevOps through NestJS API.
    {
      provide: WORK_ITEM_STORE,
      useClass: AzureDevOpsWorkItemStore,
    },
  ],
};