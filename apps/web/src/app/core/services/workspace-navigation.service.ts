import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ViewKey } from '../../shared/models/view-key.model';
import { WorkItem } from '../../shared/models/work-item.model';

const ROUTE_BY_VIEW: Record<ViewKey, string> = {
  overview: '/',
  'work-items': '/work-items',
  documents: '/documents',
  integrations: '/integrations',
};

/** Coordinates route changes and one-time UI requests between feature pages. */
@Injectable({ providedIn: 'root' })
export class WorkspaceNavigationService {
  private readonly router = inject(Router);

  readonly promptSeed = signal('');
  readonly editRequest = signal<WorkItem | null>(null);

  navigateTo(view: ViewKey): void {
    this.promptSeed.set('');
    this.editRequest.set(null);
    void this.router.navigateByUrl(ROUTE_BY_VIEW[view]);
  }

  navigateWithPrompt(prompt: string): void {
    this.promptSeed.set(prompt);
    this.editRequest.set(null);
    void this.router.navigateByUrl('/');
  }

  requestEdit(item: WorkItem): void {
    this.promptSeed.set('');
    this.editRequest.set({ ...item });
    void this.router.navigateByUrl('/work-items');
  }

  clearPromptSeed(): void {
    this.promptSeed.set('');
  }

  clearEditRequest(): void {
    this.editRequest.set(null);
  }
}
