import { InMemoryWorkItemStore } from './in-memory-work-item.store';

describe('InMemoryWorkItemStore', () => {
  let store: InMemoryWorkItemStore;

  beforeEach(() => {
    store = new InMemoryWorkItemStore();
  });

  it('restores an independent copy of the seed work items', async () => {
    expect(store.items().length).toBe(9);

    await store.delete(101);
    store.resetDemoData();

    expect(store.items().length).toBe(9);
    expect(store.findById(101)?.title).toBe('User Management Platform');
  });

  it('creates and updates work items', async () => {
    const created = await store.create({
      type: 'Task',
      title: 'Add validation tests',
      state: 'New',
      assignedTo: 'Unassigned',
      priority: 'Medium',
      parentId: 103,
    });

    await store.update(created.id, { state: 'Active', assignedTo: 'Alex Morgan' });

    expect(store.findById(created.id)).toMatchObject({
      state: 'Active',
      assignedTo: 'Alex Morgan',
    });
  });

  it('deletes one selected item and detaches, rather than cascading, its children', async () => {
    await store.delete(103);

    expect(store.findById(103)).toBeUndefined();
    expect(store.findById(104)).toBeDefined();
    expect(store.findById(104)?.parentId).toBeUndefined();
  });
});
