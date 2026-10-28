import type { TreeNode } from 'primeng/api';
import type { WorkItem } from '../../../shared/models/work-item.model';

/**
 * Converts flat work-item records into PrimeNG TreeTable nodes.
 * Matching children retain their parent chain when filters hide the parent.
 * Missing parents and malformed cyclic relationships are handled as roots.
 */
export function buildWorkItemTree(
  allItems: readonly WorkItem[],
  matchingItems: readonly WorkItem[],
): TreeNode[] {
  const itemsById = new Map(allItems.map((item) => [item.id, item]));
  const includedIds = new Set<number>();

  for (const match of matchingItems) {
    let current: WorkItem | undefined = match;
    const visited = new Set<number>();

    while (current && !visited.has(current.id)) {
      visited.add(current.id);
      includedIds.add(current.id);
      current = current.parentId == null ? undefined : itemsById.get(current.parentId);
    }
  }

  const nodesById = new Map<number, TreeNode>();
  for (const item of allItems) {
    if (!includedIds.has(item.id)) continue;

    nodesById.set(item.id, {
      key: String(item.id),
      data: item,
      leaf: true,
      expanded: false,
    });
  }

  const roots: TreeNode[] = [];

  for (const item of allItems) {
    const node = nodesById.get(item.id);
    if (!node) continue;

    const parentId = item.parentId;
    const parent = parentId == null ? undefined : nodesById.get(parentId);

    if (
      parentId == null ||
      !parent ||
      parent === node ||
      wouldCreateCycle(item.id, parentId, itemsById)
    ) {
      roots.push(node);
      continue;
    }

    parent.children ??= [];
    parent.children.push(node);
    parent.leaf = false;
  }

  for (const node of nodesById.values()) {
    node.expanded = Boolean(node.children?.length);
  }

  return roots;
}

function wouldCreateCycle(
  childId: number,
  parentId: number,
  itemsById: ReadonlyMap<number, WorkItem>,
): boolean {
  let current: WorkItem | undefined = itemsById.get(parentId);
  const visited = new Set<number>();

  while (current) {
    if (current.id === childId || visited.has(current.id)) return true;
    visited.add(current.id);
    current = current.parentId == null ? undefined : itemsById.get(current.parentId);
  }

  return false;
}
