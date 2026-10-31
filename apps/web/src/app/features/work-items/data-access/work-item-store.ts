import { InjectionToken, Signal } from '@angular/core';

import { WorkItem } from '../../../shared/models/work-item.model';
import { WorkItemsQuery } from '../../../shared/models/work-items-query.model';

export interface WorkItemCounts {
  total: number;
  active: number;
  newItems: number;
  completed: number;
}

export interface WorkItemStore {
  readonly items: Signal<WorkItem[]>;

  // Server-side pagination
  readonly totalRecords: Signal<number>;

  refresh(query?: WorkItemsQuery): Promise<void>;

  create(
    item: Omit<WorkItem, 'id' | 'updatedAt'>,
  ): Promise<WorkItem>;

  update(
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
  ): Promise<void>;

  delete(id: number): Promise<void>;

  resetDemoData?(): void;

  getCounts(): WorkItemCounts;
}

// Dependency injection token
export const WORK_ITEM_STORE = new InjectionToken<WorkItemStore>(
  'WORK_ITEM_STORE',
);