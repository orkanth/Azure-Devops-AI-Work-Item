export type WorkItemType = 'Epic' | 'Feature' | 'User Story' | 'Task' | 'Bug';
export type WorkItemState = 'New' | 'Active' | 'Resolved' | 'Closed';
export type WorkItemPriority = 'Low' | 'Medium' | 'High';

export interface WorkItem {
  id: number;
  type: WorkItemType;
  title: string;
  state: WorkItemState;
  assignedTo: string;
  priority: WorkItemPriority;
  parentId?: number;
  updatedAt: string;
}

export type WorkItemActionKind = 'create' | 'update' | 'assign' | 'delete';

export interface PromptProposal {
  kind: WorkItemActionKind | 'ambiguous' | 'unknown';
  actionKind?: WorkItemActionKind;
  description: string;
  target?: WorkItem;
  candidates?: WorkItem[];
  newItem?: Partial<WorkItem>;
  changes?: Partial<WorkItem>;
  assignee?: string;
  error?: string;
}
