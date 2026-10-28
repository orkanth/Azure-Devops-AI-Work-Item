import type { WorkItem } from '../../../shared/models/work-item.model';
import { buildWorkItemTree } from './work-item-tree.util';

const sampleItems: WorkItem[] = [
  {
    id: 101,
    type: 'Epic',
    title: 'User Management',
    state: 'Active',
    assignedTo: 'Priya Shah',
    priority: 'High',
    updatedAt: 'Today',
  },
  {
    id: 102,
    type: 'Feature',
    title: 'Authentication',
    state: 'Active',
    assignedTo: 'Alex Morgan',
    priority: 'High',
    parentId: 101,
    updatedAt: 'Today',
  },
  {
    id: 103,
    type: 'User Story',
    title: 'Login',
    state: 'Active',
    assignedTo: 'Alex Morgan',
    priority: 'High',
    parentId: 102,
    updatedAt: 'Today',
  },
  {
    id: 104,
    type: 'Task',
    title: 'Validate input',
    state: 'New',
    assignedTo: 'Unassigned',
    priority: 'Medium',
    parentId: 103,
    updatedAt: 'Today',
  },
];

describe('buildWorkItemTree', () => {
  it('builds a nested Epic > Feature > User Story > Task hierarchy', () => {
    const roots = buildWorkItemTree(sampleItems, sampleItems);

    expect(roots).toHaveLength(1);
    expect(roots[0]?.data.title).toBe('User Management');
    expect(roots[0]?.children?.[0]?.data.title).toBe('Authentication');
    expect(roots[0]?.children?.[0]?.children?.[0]?.children?.[0]?.data.title).toBe(
      'Validate input',
    );
    expect(roots[0]?.expanded).toBe(true);
    expect(roots[0]?.children?.[0]?.expanded).toBe(true);
    expect(roots[0]?.children?.[0]?.children?.[0]?.expanded).toBe(true);
  });

  it('keeps parent ancestors when only a child matches a filter', () => {
    const roots = buildWorkItemTree(sampleItems, [sampleItems[3]!]);

    expect(roots[0]?.data.id).toBe(101);
    expect(roots[0]?.children?.[0]?.children?.[0]?.children?.[0]?.data.id).toBe(104);
  });

  it('returns no nodes when there are no matching items', () => {
    expect(buildWorkItemTree(sampleItems, [])).toEqual([]);
  });

  it('avoids cyclic parent relationships', () => {
    const cyclicItems: WorkItem[] = [
      { ...sampleItems[0]!, id: 201, parentId: 202 },
      { ...sampleItems[1]!, id: 202, parentId: 201 },
    ];

    const roots = buildWorkItemTree(cyclicItems, cyclicItems);
    expect(roots).toHaveLength(2);
    expect(roots.every((node) => !node.children?.length)).toBe(true);
  });
});
