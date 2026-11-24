
export interface ChatRequest {
  question: string;
  conversation_id?: string;
  project_id?: string;
}

export interface ChatWorkItem {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedTo?: string;
  assignedToEmail?: string;
  description?: string;
  acceptanceCriteria?: string;
  priority?: string;
  parentId?: number;
  updatedAt?: string;
  url?: string;
}

// Work item returned by the AI generation proposal
export interface GeneratedWorkItem {
  title: string;
  type: string;
  description?: string;
  acceptance_criteria?: string[];
  children?: GeneratedWorkItem[];
}

// Work item successfully published to Azure DevOps
export interface PublishedWorkItem {
  id: number;
  type: string;
  title: string;
  url?: string;
}

export interface PublishingSummary {
  created: number;
  reused: number;
  failed: number;
}

export interface PublishingResult {
  success?: boolean;
  status?: string;
  created?: PublishedWorkItem[];
  reused?: PublishedWorkItem[];
  summary?: PublishingSummary;
  message?: string;
}

export interface GenerationProposal {
  requested_type?: string;
  items?: GeneratedWorkItem[];
}

export interface ChatResponse {
  conversation_id: string;
  status: 'success' | 'error' | 'completed' | 'clarification_required';
  agent_response: string;
  intent?: string | null;
  filters: Record<string, unknown>;
  tool_results: ChatWorkItem[];
  sources: Array<Record<string, unknown>>;
  clarification_options: Array<Record<string, unknown>>;
  error?: string | null;
  work_item_intent?: string | null;
  proposal?: GenerationProposal | null;
  publish_id?: string | null;
  publishing_result?: PublishingResult | null;
}
