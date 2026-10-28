import { CommonModule } from '@angular/common';
import { Component, effect, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppFeedbackService } from '../../../core/services/app-feedback.service';
import { WorkspaceNavigationService } from '../../../core/services/workspace-navigation.service';
import { WorkItemTableComponent } from '../../../shared/components/work-item-table/work-item-table.component';
import {
  WorkItem,
  WorkItemPriority,
  WorkItemState,
  WorkItemType,
} from '../../../shared/models/work-item.model';
import { WORK_ITEM_STORE } from '../data-access/work-item-store';
import {
  WorkItemEditDialogComponent,
  type WorkItemEditResult,
} from '../components/work-item-edit-dialog/work-item-edit-dialog.component';

@Component({
  selector: 'app-work-items-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    WorkItemEditDialogComponent,
    WorkItemTableComponent,
  ],
  templateUrl: './work-items-page.component.html',
  styleUrl: './work-items-page.component.css',
})
export class WorkItemsPageComponent {
  private readonly workItemStore = inject(WORK_ITEM_STORE);
  private readonly feedback = inject(AppFeedbackService);
  private readonly navigation = inject(WorkspaceNavigationService);

  constructor() {
    effect(() => {
      const item = this.navigation.editRequest();
      if (item) {
        this.startEdit(item);
        this.navigation.clearEditRequest();
      }
    });
  }

  readonly items = this.workItemStore.items;
  readonly supportsDemoReset = typeof this.workItemStore.resetDemoData === 'function';
  readonly workItemTypes: WorkItemType[] = ['Epic', 'Feature', 'User Story', 'Task'];
  readonly workItemStates: WorkItemState[] = ['New', 'Active', 'Resolved', 'Closed'];
  readonly priorities: WorkItemPriority[] = ['Low', 'Medium', 'High'];

  searchTerm = '';
  typeFilter = 'All types';
  stateFilter = 'All states';
  editingItem: WorkItem | null = null;
  deleteTarget: WorkItem | null = null;
  deleteAcknowledged = false;

  get filteredItems(): WorkItem[] {
    const query = this.searchTerm.trim().toLowerCase();
    return this.items().filter((item) => {
      const searchableText = `${item.id} ${item.title} ${item.assignedTo} ${item.type}`;
      const matchesSearch = !query || searchableText.toLowerCase().includes(query);
      const matchesType = this.typeFilter === 'All types' || item.type === this.typeFilter;
      const matchesState = this.stateFilter === 'All states' || item.state === this.stateFilter;

      return matchesSearch && matchesType && matchesState;
    });
  }

  startCreatePrompt(): void {
    this.navigation.navigateWithPrompt('Create a task for ');
  }

  navigateToCommands(): void {
    this.navigation.navigateTo('overview');
  }

  startEdit(item: WorkItem): void {
    this.editingItem = { ...item };
  }

  closeEdit(): void {
    this.editingItem = null;
  }

  async saveEdit(result: WorkItemEditResult): Promise<void> {
    try {
      await this.workItemStore.update(result.id, result.changes);
      this.closeEdit();
      this.feedback.show(
        'Work item updated in local demo data. Azure DevOps is not connected yet.',
        'success',
      );
    } catch {
      this.feedback.show('The work item could not be updated. Please try again.', 'error');
    }
  }

  prepareDelete(item: WorkItem): void {
    this.deleteTarget = { ...item };
    this.deleteAcknowledged = false;
    this.feedback.clear();
  }

  cancelDelete(): void {
    this.deleteTarget = null;
    this.deleteAcknowledged = false;
  }

  async confirmDelete(): Promise<void> {
    const target = this.deleteTarget;
    if (!target || !this.deleteAcknowledged) return;

    try {
      await this.workItemStore.delete(target.id);
      this.cancelDelete();
      this.feedback.show(
        `Deleted demo work item #${target.id}: ${target.title}. Child items were kept and detached from the deleted parent. Azure DevOps is not connected yet.`,
        'success',
      );
    } catch {
      this.feedback.show('The work item could not be deleted. Please try again.', 'error');
    }
  }

  resetDemo(): void {
    if (!this.workItemStore.resetDemoData) return;

    this.workItemStore.resetDemoData();
    this.cancelDelete();
    this.searchTerm = '';
    this.typeFilter = 'All types';
    this.stateFilter = 'All states';
    this.feedback.show('Sample work items restored.', 'info');
  }
}
