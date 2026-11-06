import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { WorkItemsQuery } from '../../../shared/models/work-items-query.model';

import {
  ApiService,
  ApiWorkItem,
  CreateApiWorkItemRequest,
  UpdateApiWorkItemRequest,
} from '../../../core/services/api.service';

import {
  WorkItem,
  WorkItemPriority,
  WorkItemType,
} from '../../../shared/models/work-item.model';

import type { WorkItemStore, WorkItemCounts } from './work-item-store';

@Injectable()
export class AzureDevOpsWorkItemStore implements WorkItemStore {
  private readonly apiService = inject(ApiService);

  private readonly _items = signal<WorkItem[]>([]);

  readonly items = this._items.asReadonly();
  private readonly _totalRecords = signal(0);

  readonly totalRecords = this._totalRecords.asReadonly();
  private currentQuery: WorkItemsQuery = {
    page: 1,
    pageSize: 10,
    sortBy: 'id',
    sortOrder: 'DESC',
  };

  async refresh(): Promise<void> {
    const response = await firstValueFrom(
      this.apiService.getWorkItems({
        page: 1,
        pageSize: 200,
        sortBy: 'id',
        sortOrder: 'DESC',
      }),
    );

    if (!Array.isArray(response)) {
      console.error('Unexpected API response:', response);
      throw new Error('Invalid work items API response.');
    }

    this._items.set(response.map((item) => this.mapWorkItem(item)));

    this._totalRecords.set(response.length);
  }

  async create(item: Omit<WorkItem, 'id' | 'updatedAt'>): Promise<WorkItem> {
    const payload: CreateApiWorkItemRequest = {
      type: item.type,
      title: item.title,
      description: item.description,
      acceptanceCriteria: item.acceptanceCriteria,
      assignedTo:
        item.assignedToEmail ||
        (item.assignedTo !== 'Unassigned' ? item.assignedTo : undefined),
      priority: item.priority,
      parentId: item.parentId,
    };

    // Call POST instead of GET.
    const response = await firstValueFrom(
      this.apiService.createWorkItem(payload),
    );

    // POST returns one work item, not a paginated collection.
    const created = this.mapWorkItem(response);

    // Update local state only after Azure DevOps confirms creation.
    this._items.update((current) => [
      created,
      ...current.filter((existing) => existing.id !== created.id),
    ]);

    return created;
  }

  async update(
    id: number,
    changes: Partial<
      Pick<
        WorkItem,
        | 'title'
        | 'description'
        | 'acceptanceCriteria'
        | 'state'
        | 'assignedTo'
        | 'priority'
      >
    >,
  ): Promise<void> {
    const payload: UpdateApiWorkItemRequest = {
      ...(changes.title !== undefined && { title: changes.title }),
      ...(changes.description !== undefined && {
        description: changes.description,
      }),
      ...(changes.acceptanceCriteria !== undefined && {
        acceptanceCriteria: changes.acceptanceCriteria,
      }),
      ...(changes.state !== undefined && { state: changes.state }),
      ...(changes.assignedTo !== undefined && {
        assignedTo: changes.assignedTo,
      }),
      ...(changes.priority !== undefined && {
        priority: changes.priority,
      }),
    };

    const response = await firstValueFrom(
      this.apiService.updateWorkItem(id, payload),
    );

    const updated = this.mapWorkItem(response);
    const existing = this.findById(id);

    this._items.update((current) =>
      current.map((item) =>
        item.id === id
          ? {
              ...updated,
              parentId: updated.parentId ?? existing?.parentId,
            }
          : item,
      ),
    );
  }

  async delete(id: number): Promise<void> {
    await firstValueFrom(this.apiService.deleteWorkItem(id));

    // Remove locally only after Azure DevOps confirms deletion.
    this._items.update((current) => current.filter((item) => item.id !== id));

    // Refresh because deleting a parent can affect child relationships.
    await this.refresh();
  }

  private mapWorkItem(item: ApiWorkItem): WorkItem {
    return {
      id: item.id,
      title: item.title,
      type: item.type,
      description: item.description,
      acceptanceCriteria: item.acceptanceCriteria,
      state: item.state,
      assignedTo: item.assignedTo || 'Unassigned',
      assignedToEmail: item.assignedToEmail,
      priority: this.mapPriority(item.priority),
      parentId: item.parentId,
      updatedAt: item.updatedAt,
      url: item.url,
      isContextOnly: item.isContextOnly ?? false,
    };
  }

  private mapType(type: string): WorkItemType {
    const supportedTypes: WorkItemType[] = [
      'Epic',
      'Feature',
      'User Story',
      'Task',
      'Bug',
    ];

    if (!supportedTypes.includes(type as WorkItemType)) {
      throw new Error(`Unsupported Azure DevOps work item type: ${type}`);
    }

    return type as WorkItemType;
  }

  private mapPriority(priority: string): WorkItemPriority {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'High';
      case 'low':
        return 'Low';
      default:
        return 'Medium';
    }
  }

  findById(id: number): WorkItem | undefined {
    return this._items().find((item) => item.id === id);
  }

  getCounts(): WorkItemCounts {
    const items = this._items();

    return {
      total: items.length,
      active: items.filter((item) =>
        ['active', 'in progress'].includes(item.state.toLowerCase()),
      ).length,
      newItems: items.filter((item) =>
        ['new', 'to do'].includes(item.state.toLowerCase()),
      ).length,
      completed: items.filter((item) =>
        ['resolved', 'closed', 'done'].includes(item.state.toLowerCase()),
      ).length,
    };
  }
}
