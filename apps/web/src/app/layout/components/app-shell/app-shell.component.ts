import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter, startWith } from 'rxjs';
import { AppFeedbackService } from '../../../core/services/app-feedback.service';
import { WORK_ITEM_STORE } from '../../../features/work-items/data-access/work-item-store';
import { WorkspaceNavigationService } from '../../../core/services/workspace-navigation.service';
import { ViewKey } from '../../../shared/models/view-key.model';
import { AppFooterComponent } from '../app-footer/app-footer.component';
import { AppHeaderComponent } from '../app-header/app-header.component';
import { AppNavComponent } from '../app-nav/app-nav.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    AppNavComponent,
    AppHeaderComponent,
    AppFooterComponent,
  ],
  templateUrl: './app-shell.component.html',
  styleUrl: './app-shell.component.css',
})
export class AppShellComponent {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);
  private readonly navigation = inject(WorkspaceNavigationService);
  private readonly workItemService = inject(WORK_ITEM_STORE);

  readonly feedback = inject(AppFeedbackService);
  readonly items = this.workItemService.items;
  readonly currentYear = new Date().getFullYear();
  readonly pageTitle = signal('AI command center');
  readonly visibleTitle = this.pageTitle;

  constructor() {
    void this.workItemService.refresh().catch(() => {
      this.feedback.show('Workspace data could not be loaded. Please try again.', 'error');
    });

    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        startWith(null),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.syncPageTitle());
  }

  openView(view: ViewKey): void {
    this.navigation.navigateTo(view);
    this.feedback.clear();
  }

  fillPrompt(prompt: string): void {
    this.navigation.navigateWithPrompt(prompt);
    this.feedback.clear();
  }

  private syncPageTitle(): void {
    let route = this.activatedRoute;
    while (route.firstChild) {
      route = route.firstChild;
    }

    this.pageTitle.set(route.snapshot.data['pageTitle'] ?? 'Workspace');
  }
}
