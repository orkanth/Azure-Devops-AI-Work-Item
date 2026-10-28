import { CommonModule } from '@angular/common';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import type { TreeNode } from 'primeng/api';
import { TreeTableModule } from 'primeng/treetable';
import { AppFeedbackService } from '../../../core/services/app-feedback.service';
import { WorkspaceNavigationService } from '../../../core/services/workspace-navigation.service';
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
import { buildWorkItemTree } from '../utils/work-item-tree.util';

@Component({
  selector: 'app-work-items-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TreeTableModule, WorkItemEditDialogComponent],
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
  readonly workItemTypes: WorkItemType[] = ['Epic', 'Feature', 'User Story', 'Task', 'Bug'];
  readonly workItemStates: WorkItemState[] = ['New', 'Active', 'Resolved', 'Closed'];
  readonly priorities: WorkItemPriority[] = ['Low', 'Medium', 'High'];

  readonly searchTerm = signal('');
  readonly typeFilter = signal('All types');
  readonly stateFilter = signal('All states');

  readonly matchingItems = computed<WorkItem[]>(() => {
    const query = this.searchTerm().trim().toLowerCase();
    const typeFilter = this.typeFilter();
    const stateFilter = this.stateFilter();

    return this.items().filter((item) => {
      const searchableText = `${item.id} ${item.title} ${item.assignedTo} ${item.type} ${item.state}`;
      const matchesSearch = !query || searchableText.toLowerCase().includes(query);
      const matchesType = typeFilter === 'All types' || item.type === typeFilter;
      const matchesState = stateFilter === 'All states' || item.state === stateFilter;

      return matchesSearch && matchesType && matchesState;
    });
  });

  /** The computed value stays stable until items or filters change, preserving expanded rows. */
  readonly treeNodes = computed<TreeNode[]>(() =>
    buildWorkItemTree(this.items(), this.matchingItems()),
  );

  readonly visibleTreeNodeCount = computed(() => countTreeNodes(this.treeNodes()));

  editingItem: WorkItem | null = null;
  deleteTarget: WorkItem | null = null;
  deleteAcknowledged = false;

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

  resetFilters(): void {
    this.searchTerm.set('');
    this.typeFilter.set('All types');
    this.stateFilter.set('All states');
  }

  resetDemo(): void {
    if (!this.workItemStore.resetDemoData) return;

    this.workItemStore.resetDemoData();
    this.cancelDelete();
    this.resetFilters();
    this.feedback.show('Sample work items restored.', 'info');
  }

  typeClass(type: WorkItemType): string {
    return type.toLowerCase().replace(/\s+/g, '-');
  }

  typeLetter(type: WorkItemType): string {
    return type === 'User Story' ? 'S' : type.charAt(0).toUpperCase();
  }

  stateClass(state: WorkItemState): string {
    return state.toLowerCase().replace(/\s+/g, '-');
  }

  initials(name: string): string {
    if (!name || name === 'Unassigned') return '?';
    return name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join('');
  }

  parentTitle(parentId: number | undefined): string {
    if (parentId == null) return '—';
    const parent = this.items().find((item) => item.id === parentId);
    return parent ? `#${parent.id} ${parent.title}` : `#${parentId}`;
  }
}

function countTreeNodes(nodes: TreeNode[]): number {
  return nodes.reduce((count, node) => count + 1 + countTreeNodes(node.children ?? []), 0);
}
