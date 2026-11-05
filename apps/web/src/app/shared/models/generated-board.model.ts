
export interface GeneratedTask {
  title: string;
  description: string;
  acceptance_criteria: string[];
}

export interface GeneratedUserStory {
  title: string;
  description: string;
  acceptance_criteria: string[];
  tasks: GeneratedTask[];
}

export interface GeneratedFeature {
  title: string;
  description: string;
  user_stories: GeneratedUserStory[];
}

export interface GeneratedEpic {
  title: string;
  description: string;
  features: GeneratedFeature[];
}

export interface GenerateBoardRequest {
  requirement: string;
}

export interface GenerateBoardResponse {
  status: string;
  message: string;
  requirement: string;
  epic: GeneratedEpic | null;
}
