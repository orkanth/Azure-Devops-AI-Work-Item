import { Routes } from '@angular/router';
import { AppShellComponent } from './layout/components/app-shell/app-shell.component';

/**
 * Application route table.
 * Feature pages are lazy-loaded so the shell stays small and route-specific
 * code is only requested when the user opens that area.
 */
export const appRoutes: Routes = [
  {
    path: '',
    component: AppShellComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        title: 'WorkPilot AI | Command Center',
        data: { pageTitle: 'AI command center' },
        loadComponent: () =>
          import('./features/overview/pages/overview-page.component').then(
            ({ OverviewPageComponent }) => OverviewPageComponent,
          ),
      },
      {
        path: 'work-items',
        title: 'WorkPilot AI | Work Items',
        data: { pageTitle: 'Work items' },
        loadComponent: () =>
          import('./features/work-items/pages/work-items-page.component').then(
            ({ WorkItemsPageComponent }) => WorkItemsPageComponent,
          ),
      },
      {
        path: 'documents',
        title: 'WorkPilot AI | Documents & RAG',
        data: { pageTitle: 'Documents & knowledge' },
        loadComponent: () =>
          import('./features/documents/pages/documents-page.component').then(
            ({ DocumentsPageComponent }) => DocumentsPageComponent,
          ),
      },
      {
        path: 'integrations',
        title: 'WorkPilot AI | Integrations',
        data: { pageTitle: 'Integrations' },
        loadComponent: () =>
          import('./features/integrations/pages/integrations-page.component').then(
            ({ IntegrationsPageComponent }) => IntegrationsPageComponent,
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: '',
  },
];
