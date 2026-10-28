import { InjectionToken, Signal } from '@angular/core';
import { WorkItem } from '../../../shared/models/work-item.model';

export interface WorkItemCounts {
  total: number;
  active: number;
  newItems: number;
  completed: number;
}

/** Async data-access contract used by feature pages. The current implementation is demo-only. */
export interface WorkItemStore {
  readonly items: Signal<WorkItem[]>;
  refresh(): Promise<void>;
  create(item: Omit<WorkItem, 'id' | 'updatedAt'>): Promise<WorkItem>;
  update(
    id: number,
    changes: Partial<
      Pick<WorkItem, 'title' | 'type' | 'state' | 'assignedTo' | 'priority' | 'parentId'>
    >,
  ): Promise<void>;
  delete(id: number): Promise<void>;
  findById(id: number): WorkItem | undefined;
  /** Available only for a demo adapter; production stores should omit this capability. */
  resetDemoData?(): void;
  getCounts(): WorkItemCounts;
}

export const WORK_ITEM_STORE = new InjectionToken<WorkItemStore>('WORK_ITEM_STORE');
