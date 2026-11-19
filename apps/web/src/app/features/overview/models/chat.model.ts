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
  proposal?: Record<string, unknown> | null;
  publish_id?: string | null;
  publishing_result?: Record<string, unknown> | null;
}