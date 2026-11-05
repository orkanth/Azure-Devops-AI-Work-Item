
import {
  BadGatewayException,
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';

import { GenerateBoardDto } from './dto/generate-board.dto';

interface GeneratedTask {
  title: string;
  description: string;
  acceptance_criteria: string[];
}

interface GeneratedUserStory {
  title: string;
  description: string;
  acceptance_criteria: string[];
  tasks: GeneratedTask[];
}

interface GeneratedFeature {
  title: string;
  description: string;
  user_stories: GeneratedUserStory[];
}

interface GeneratedEpic {
  title: string;
  description: string;
  features: GeneratedFeature[];
}

interface GenerateBoardResponse {
  status: string;
  message: string;
  requirement: string;
  epic: GeneratedEpic | null;
}

@Injectable()
export class GenerationService {
  private readonly logger = new Logger(GenerationService.name);

  async generateBoard(
    dto: GenerateBoardDto,
  ): Promise<GenerateBoardResponse> {
    const aiServiceUrl = (
      process.env.AI_SERVICE_URL || 'http://localhost:8000'
    ).replace(/\/+$/, '');

    try {
      const response = await fetch(
        `${aiServiceUrl}/api/v1/work-items/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            requirement: dto.requirement,
          }),
          signal: AbortSignal.timeout(120000),
        },
      );

      if (!response.ok) {
        const errorBody = await response.text();

        this.logger.error(
          `AI service returned HTTP ${response.status}: ${errorBody}`,
        );

        throw new BadGatewayException(
          'AI generation service could not process the request.',
        );
      }

      return (await response.json()) as GenerateBoardResponse;
    } catch (error: unknown) {
      if (error instanceof BadGatewayException) {
        throw error;
      }

      if (
        error instanceof Error &&
        error.name === 'TimeoutError'
      ) {
        this.logger.error('AI generation request timed out.');

        throw new ServiceUnavailableException(
          'AI generation took too long. Please try again.',
        );
      }

      this.logger.error(
        'Could not connect to AI generation service.',
        error instanceof Error ? error.stack : undefined,
      );

      throw new ServiceUnavailableException(
        'AI generation service is currently unavailable.',
      );
    }
  }
}
