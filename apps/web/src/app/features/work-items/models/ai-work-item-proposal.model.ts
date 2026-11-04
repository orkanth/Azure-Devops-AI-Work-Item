export interface AiTaskProposal {
  title: string;
  description: string;
  acceptance_criteria: string[];
}

export interface AiUserStoryProposal {
  title: string;
  description: string;
  acceptance_criteria: string[];
  tasks: AiTaskProposal[];
}

export interface AiFeatureProposal {
  title: string;
  description: string;
  user_stories: AiUserStoryProposal[];
}

export interface AiEpicProposal {
  title: string;
  description: string;
  features: AiFeatureProposal[];
}

export interface GenerateWorkItemsRequest {
  requirement: string;
}

export interface GenerateWorkItemsResponse {
  status: string;
  message: string;
  requirement: string;
  epic: AiEpicProposal | null;
}