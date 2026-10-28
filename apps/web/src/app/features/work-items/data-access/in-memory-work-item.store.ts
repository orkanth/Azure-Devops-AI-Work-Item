import { Injectable, signal } from '@angular/core';
import { WorkItem } from '../../../shared/models/work-item.model';
import { WorkItemCounts, WorkItemStore } from './work-item-store';

const INITIAL_WORK_ITEMS: WorkItem[] = [
  {
    id: 101,
    type: 'Epic',
    title: 'User Management Platform',
    state: 'Active',
    assignedTo: 'Priya Shah',
    priority: 'High',
    updatedAt: 'Today',
  },
  {
    id: 102,
    type: 'Feature',
    title: 'Authentication and Access Control',
    state: 'Active',
    assignedTo: 'Alex Morgan',
    priority: 'High',
    parentId: 101,
    updatedAt: 'Today',
  },
  {
    id: 103,
    type: 'User Story',
    title: 'Login with email and password',
    state: 'Active',
    assignedTo: 'Alex Morgan',
    priority: 'High',
    parentId: 102,
    updatedAt: 'Today',
  },
  {
    id: 104,
    type: 'Task',
    title: 'Add API input validation',
    state: 'New',
    assignedTo: 'Unassigned',
    priority: 'High',
    parentId: 103,
    updatedAt: 'Yesterday',
  },
  {
    id: 105,
    type: 'Task',
    title: 'Build Angular login form',
    state: 'Active',
    assignedTo: 'Maya Patel',
    priority: 'Medium',
    parentId: 103,
    updatedAt: 'Yesterday',
  },
  {
    id: 106,
    type: 'Task',
    title: 'Write authentication unit tests',
    state: 'New',
    assignedTo: 'Unassigned',
    priority: 'Medium',
    parentId: 103,
    updatedAt: 'Oct 19',
  },
  {
    id: 107,
    type: 'User Story',
    title: 'Reset a forgotten password',
    state: 'New',
    assignedTo: 'Sam Taylor',
    priority: 'Medium',
    parentId: 102,
    updatedAt: 'Oct 18',
  },
  {
    id: 108,
    type: 'Feature',
    title: 'User profile and administration',
    state: 'New',
    assignedTo: 'Priya Shah',
    priority: 'Medium',
    parentId: 101,
    updatedAt: 'Oct 17',
  },
  {
    id: 109,
    type: 'Task',
    title: 'Record user access audit events',
    state: 'Resolved',
    assignedTo: 'Maya Patel',
    priority: 'Low',
    parentId: 108,
    updatedAt: 'Oct 16',
  },
  {
    id: 110,
    type: 'Bug',
    title: 'Password reset link validation fails',
    state: 'New',
    assignedTo: 'Unassigned',
    priority: 'High',
    parentId: 107,
    updatedAt: 'Today',
  },
];

/** In-memory adapter used only while the Azure DevOps API is not connected. */
@Injectable()
export class InMemoryWorkItemStore implements WorkItemStore {
  readonly items = signal<WorkItem[]>(this.cloneInitialItems());
  private nextId = 111;

  /** Seed data is already available locally, so refreshing the demo store is a no-op. */
  refresh(): Promise<void> {
    return Promise.resolve();
  }

  async create(item: Omit<WorkItem, 'id' | 'updatedAt'>): Promise<WorkItem> {
    const created: WorkItem = {
      ...item,
      id: this.nextId++,
      updatedAt: 'Just now',
    };

    this.items.update((items) => [created, ...items]);
    return created;
  }

  async update(
    id: number,
    changes: Partial<
      Pick<WorkItem, 'title' | 'type' | 'state' | 'assignedTo' | 'priority' | 'parentId'>
    >,
  ): Promise<void> {
    this.items.update((items) =>
      items.map((item) =>
        item.id === id ? { ...item, ...changes, updatedAt: 'Just now' } : item,
      ),
    );
  }

  async delete(id: number): Promise<void> {
    this.items.update((items) =>
      items
        .filter((item) => item.id !== id)
        .map((item) =>
          item.parentId === id
            ? { ...item, parentId: undefined, updatedAt: 'Just now' }
            : item,
        ),
    );
  }

  findById(id: number): WorkItem | undefined {
    return this.items().find((item) => item.id === id);
  }

  resetDemoData(): void {
    this.items.set(this.cloneInitialItems());
    this.nextId = 111;
  }

  getCounts(): WorkItemCounts {
    const items = this.items();

    return {
      total: items.length,
      active: items.filter((item) => item.state === 'Active').length,
      newItems: items.filter((item) => item.state === 'New').length,
      completed: items.filter(
        (item) => item.state === 'Closed' || item.state === 'Resolved',
      ).length,
    };
  }

  private cloneInitialItems(): WorkItem[] {
    return INITIAL_WORK_ITEMS.map((item) => ({ ...item }));
  }
}
