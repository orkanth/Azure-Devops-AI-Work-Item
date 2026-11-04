import { CommonModule } from '@angular/common';
import {
  Component,
  computed,
  DestroyRef,
  effect,
  inject,
  signal,
  OnInit,
} from '@angular/core';
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
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { WorkItemsQuery } from '../../../shared/models/work-items-query.model';
import { PaginatorModule } from 'primeng/paginator';
import { AiWorkItemProposalService } from '../data-access/ai-work-item-proposal.service';
import type { AiEpicProposal } from '../models/ai-work-item-proposal.model';
@Component({
  selector: 'app-work-items-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TreeTableModule,
    WorkItemEditDialogComponent,
  ],
  templateUrl: './work-items-page.component.html',
  styleUrl: './work-items-page.component.css',
})
export class WorkItemsPageComponent implements OnInit {
  private readonly workItemStore = inject(WORK_ITEM_STORE);
  private readonly feedback = inject(AppFeedbackService);
  private readonly navigation = inject(WorkspaceNavigationService);
  // Loading states
  readonly isLoading = signal(true);
  readonly updatingItemId = signal<number | null>(null);
  readonly deletingItemId = signal<number | null>(null);

  readonly actionError = signal('');

  readonly first = signal(0);
  readonly pageSize = signal(10);

  readonly totalRecords = this.workItemStore.totalRecords;

  readonly sortBy = signal<'id' | 'title' | 'state' | 'priority'>('id');
  readonly sortOrder = signal<'ASC' | 'DESC'>('DESC');

  private readonly searchChanges$ = new Subject<string>();
  private readonly destroyRef = inject(DestroyRef);

  private readonly aiProposalService = inject(AiWorkItemProposalService);

  readonly showAiProposalDialog = signal(false);
  readonly aiRequirement = signal('');
  readonly isGeneratingProposal = signal(false);
  readonly aiProposal = signal<AiEpicProposal | null>(null);
  readonly aiProposalError = signal('');

  constructor() {
    this.searchChanges$
      .pipe(
        debounceTime(350),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        this.first.set(0);
        void this.loadWorkItems();
      });
  }

  readonly items = this.workItemStore.items;
  readonly supportsDemoReset =
    typeof this.workItemStore.resetDemoData === 'function';
  readonly workItemTypes: WorkItemType[] = [
    'Epic',
    'Feature',
    'User Story',
    'Task',
    'Bug',
  ];
  readonly workItemStates: WorkItemState[] = [
    'New',
    'Active',
    'Resolved',
    'Closed',
  ];
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
      const matchesSearch =
        !query || searchableText.toLowerCase().includes(query);
      const matchesType =
        typeFilter === 'All types' || item.type === typeFilter;
      const matchesState =
        stateFilter === 'All states' || item.state === stateFilter;

      return matchesSearch && matchesType && matchesState;
    });
  });

  /** The computed value stays stable until items or filters change, preserving expanded rows. */
  readonly treeNodes = computed<TreeNode[]>(() =>
    buildWorkItemTree(this.items(), this.matchingItems()),
  );

  readonly visibleTreeNodeCount = computed(() =>
    countTreeNodes(this.treeNodes()),
  );

  editingItem: WorkItem | null = null;
  deleteTarget: WorkItem | null = null;
  deleteAcknowledged = false;

  async ngOnInit(): Promise<void> {
    this.isLoading.set(true);

    try {
      await this.workItemStore.refresh();
    } catch (error) {
      console.error('Failed to load Azure DevOps work items:', error);

      this.feedback.show(
        'Unable to load work items from Azure DevOps.',
        'error',
      );
    } finally {
      this.isLoading.set(false);
    }
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

  async saveEdit(event: WorkItemEditResult): Promise<void> {
    if (this.updatingItemId() !== null) return;

    this.updatingItemId.set(event.id);
    this.actionError.set('');

    try {
      await this.workItemStore.update(event.id, event.changes);

      this.closeEdit();
    } catch (error) {
      console.error('Failed to update work item:', error);
      this.actionError.set('Unable to update the work item. Please try again.');
    } finally {
      this.updatingItemId.set(null);
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
    if (this.deletingItemId() !== null) return;

    this.deletingItemId.set(target.id);
    this.actionError.set('');

    try {
      await this.workItemStore.delete(target.id);

      this.cancelDelete();
    } catch (error) {
      console.error('Failed to delete work item:', error);
      this.actionError.set('Unable to delete the work item. Please try again.');
    } finally {
      this.deletingItemId.set(null);
    }
  }

  resetFilters(): void {
    this.searchTerm.set('');
    this.typeFilter.set('All types');
    this.stateFilter.set('All states');
    this.sortBy.set('id');
    this.sortOrder.set('DESC');
    this.first.set(0);

    void this.loadWorkItems();
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

  async loadWorkItems(): Promise<void> {
    this.isLoading.set(true);

    const query: WorkItemsQuery = {
      page: Math.floor(this.first() / this.pageSize()) + 1,
      pageSize: this.pageSize(),
      search: this.searchTerm().trim() || undefined,
      type: this.typeFilter() === 'All types' ? undefined : this.typeFilter(),
      state:
        this.stateFilter() === 'All states' ? undefined : this.stateFilter(),
      sortBy: this.sortBy(),
      sortOrder: this.sortOrder(),
    };

    try {
      await this.workItemStore.refresh(query);
    } catch (error) {
      console.error('Failed to load Azure DevOps work items:', error);

      this.feedback.show(
        'Unable to load work items from Azure DevOps.',
        'error',
      );
    } finally {
      this.isLoading.set(false);
    }
  }

  resetPage(): void {
    this.first.set(0);
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    this.searchChanges$.next(value);
  }

  onTypeFilterChange(value: string): void {
    this.typeFilter.set(value);
    this.first.set(0);
    void this.loadWorkItems();
  }

  onStateFilterChange(value: string): void {
    this.stateFilter.set(value);
    this.first.set(0);
    void this.loadWorkItems();
  }

  onPageChange(event: { first?: number; rows?: number }): void {
    this.first.set(event.first ?? 0);
    this.pageSize.set(event.rows ?? 10);

    void this.loadWorkItems();
  }

  onSortByChange(value: 'id' | 'title' | 'state' | 'priority'): void {
    this.sortBy.set(value);
    this.first.set(0);

    void this.loadWorkItems();
  }

  onSortOrderChange(value: 'ASC' | 'DESC'): void {
    this.sortOrder.set(value);
    this.first.set(0);

    void this.loadWorkItems();
  }

  openAiProposalDialog(): void {
    this.aiRequirement.set('');
    this.aiProposal.set(null);
    this.aiProposalError.set('');
    this.showAiProposalDialog.set(true);
  }

  closeAiProposalDialog(): void {
    if (this.isGeneratingProposal()) return;

    this.showAiProposalDialog.set(false);
  }

  async generateAiProposal(): Promise<void> {
    const requirement = this.aiRequirement().trim();

    if (requirement.length < 10) {
      this.aiProposalError.set(
        'Please enter a requirement with at least 10 characters.',
      );
      return;
    }

    this.isGeneratingProposal.set(true);
    this.aiProposalError.set('');
    this.aiProposal.set(null);

    try {
      const response = await this.aiProposalService.generateProposal({
        requirement,
      });

      if (!response.epic) {
        throw new Error('The AI returned no Epic proposal.');
      }

      this.aiProposal.set(response.epic);
    } catch (error) {
      console.error('Failed to generate AI proposal:', error);

      this.aiProposalError.set(
        'Unable to generate the proposal. Please check the AI service and try again.',
      );
    } finally {
      this.isGeneratingProposal.set(false);
    }
  }

  updateEpicField(field: 'title' | 'description', value: string): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        [field]: value,
      };
    });
  }

  updateFeatureField(
    featureIndex: number,
    field: 'title' | 'description',
    value: string,
  ): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        features: current.features.map((feature, index) =>
          index === featureIndex ? { ...feature, [field]: value } : feature,
        ),
      };
    });
  }
  updateStoryField(
    featureIndex: number,
    storyIndex: number,
    field: 'title' | 'description',
    value: string,
  ): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        features: current.features.map((feature, fIndex) =>
          fIndex === featureIndex
            ? {
                ...feature,
                user_stories: feature.user_stories.map((story, sIndex) =>
                  sIndex === storyIndex ? { ...story, [field]: value } : story,
                ),
              }
            : feature,
        ),
      };
    });
  }

  updateStoryCriteria(
    featureIndex: number,
    storyIndex: number,
    value: string,
  ): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        features: current.features.map((feature, fIndex) =>
          fIndex === featureIndex
            ? {
                ...feature,
                user_stories: feature.user_stories.map((story, sIndex) =>
                  sIndex === storyIndex
                    ? {
                        ...story,
                        acceptance_criteria: value
                          .split('\n')
                          .map((item) => item.trim())
                          .filter(Boolean),
                      }
                    : story,
                ),
              }
            : feature,
        ),
      };
    });
  }
  updateTaskField(
    featureIndex: number,
    storyIndex: number,
    taskIndex: number,
    field: 'title' | 'description',
    value: string,
  ): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        features: current.features.map((feature, fIndex) =>
          fIndex === featureIndex
            ? {
                ...feature,
                user_stories: feature.user_stories.map((story, sIndex) =>
                  sIndex === storyIndex
                    ? {
                        ...story,
                        tasks: story.tasks.map((task, tIndex) =>
                          tIndex === taskIndex
                            ? { ...task, [field]: value }
                            : task,
                        ),
                      }
                    : story,
                ),
              }
            : feature,
        ),
      };
    });
  }

  updateTaskCriteria(
    featureIndex: number,
    storyIndex: number,
    taskIndex: number,
    value: string,
  ): void {
    this.aiProposal.update((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        features: current.features.map((feature, fIndex) =>
          fIndex === featureIndex
            ? {
                ...feature,
                user_stories: feature.user_stories.map((story, sIndex) =>
                  sIndex === storyIndex
                    ? {
                        ...story,
                        tasks: story.tasks.map((task, tIndex) =>
                          tIndex === taskIndex
                            ? {
                                ...task,
                                acceptance_criteria: value
                                  .split('\n')
                                  .map((item) => item.trim())
                                  .filter(Boolean),
                              }
                            : task,
                        ),
                      }
                    : story,
                ),
              }
            : feature,
        ),
      };
    });
  }
  trackByIndex(index: number): number {
    return index;
  }
}

function countTreeNodes(nodes: TreeNode[]): number {
  return nodes.reduce(
    (count, node) => count + 1 + countTreeNodes(node.children ?? []),
    0,
  );
}
