export type WorkItemType =
  | 'Epic'
  | 'Feature'
  | 'User Story'
  | 'Task'
  | 'Bug';

export type WorkItemState = string;

export type WorkItemPriority = 'Low' | 'Medium' | 'High';

export interface WorkItem {
  id: number;
  type: WorkItemType;
  title: string;
  description?: string;
  acceptanceCriteria?: string;
  state: WorkItemState;
  assignedTo: string;
  assignedToEmail?: string;
  priority: WorkItemPriority;
  parentId?: number;
  updatedAt: string;
  url?: string;
  isContextOnly?: boolean;
}

export type WorkItemActionKind = 'create' | 'update' | 'assign' | 'delete';

export interface PromptProposal {
  kind: WorkItemActionKind | 'ambiguous' | 'unknown' | 'board';
  actionKind?: WorkItemActionKind;
  description: string;
  target?: WorkItem;
  candidates?: WorkItem[];
  newItem?: Partial<WorkItem>;
  changes?: Partial<WorkItem>;
  assignee?: string;
  error?: string;
  board?: BoardProposal;
  proposalSource?: 'prompt' | 'document';
}

export interface BoardTaskProposal {
  title: string;
  description: string;
  acceptanceCriteria: string;
}

export interface BoardUserStoryProposal {
  title: string;
  description: string;
  acceptanceCriteria: string;
  tasks: BoardTaskProposal[];
}

export interface BoardFeatureProposal {
  title: string;
  description: string;
  user_stories: BoardUserStoryProposal[];
}

export interface BoardProposal {
  title: string;
  description: string;
  features: BoardFeatureProposal[];
}