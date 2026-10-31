import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  ApiService,
  ApiWorkItem,
} from '../../../core/services/api.service';
import {
  WorkItem,
  WorkItemPriority,
  WorkItemType,
} from '../../../shared/models/work-item.model';

import type {
  WorkItemStore,
  WorkItemCounts,
} from './work-item-store';
 

@Injectable()
export class AzureDevOpsWorkItemStore implements WorkItemStore {
  private readonly apiService = inject(ApiService);

  private readonly _items = signal<WorkItem[]>([]);

  readonly items = this._items.asReadonly();

  async refresh(): Promise<void> {
    const response = await firstValueFrom(
      this.apiService.getWorkItems(),
    );

    this._items.set(
      response.map((item) => this.mapWorkItem(item)),
    );
  }

  private mapWorkItem(item: ApiWorkItem): WorkItem {
    return {
      id: item.id,
      title: item.title,
      type: item.type as WorkItemType,
      state: item.state,
      assignedTo: item.assignedTo || 'Unassigned',
      assignedToEmail: item.assignedToEmail,
      priority: this.mapPriority(item.priority),
      parentId: item.parentId,
      updatedAt: item.updatedAt,
      url: item.url,
    };
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

  async create(
    _item: Omit<WorkItem, 'id' | 'updatedAt'>,
  ): Promise<WorkItem> {
    throw new Error('Azure DevOps create endpoint is not implemented yet.');
  }

  async update(
    _id: number,
    _changes: Partial<
      Pick<
        WorkItem,
        'title' | 'type' | 'state' | 'assignedTo' | 'priority' | 'parentId'
      >
    >,
  ): Promise<void> {
    throw new Error('Azure DevOps update endpoint is not implemented yet.');
  }

  async delete(_id: number): Promise<void> {
    throw new Error('Azure DevOps delete endpoint is not implemented yet.');
  }
}