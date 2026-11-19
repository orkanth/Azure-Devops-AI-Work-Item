
import {
  BadGatewayException,
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';

import { ChatRequestDto } from './dto/chat-request.dto';

export interface ChatResponse {
  conversation_id: string;
  status: string;
  agent_response: string;
  intent?: string | null;
  filters: Record<string, unknown>;
  tool_results: unknown[];
  sources: unknown[];
  clarification_options: unknown[];
  error?: string | null;
  work_item_intent?: string | null;
  proposal?: Record<string, unknown> | null;
  publish_id?: string | null;
  publishing_result?: Record<string, unknown> | null;
}

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);

  async sendMessage(dto: ChatRequestDto): Promise<ChatResponse> {
    const aiServiceUrl = (
      process.env.AI_SERVICE_URL || 'http://localhost:8000'
    ).replace(/\/+$/, '');

    try {
      const response = await fetch(`${aiServiceUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: dto.question,
          conversation_id: dto.conversation_id,
          project_id: dto.project_id,
        }),
        signal: AbortSignal.timeout(120000),
      });

      if (!response.ok) {
        const errorBody = await response.text();

        this.logger.error(
          `AI chat service returned HTTP ${response.status}: ${errorBody}`,
        );

        throw new BadGatewayException(
          'AI chat service could not process the request.',
        );
      }

      return (await response.json()) as ChatResponse;
    } catch (error: unknown) {
      if (error instanceof BadGatewayException) {
        throw error;
      }

      if (error instanceof Error && error.name === 'TimeoutError') {
        this.logger.error('AI chat request timed out.');

        throw new ServiceUnavailableException(
          'AI chat took too long. Please try again.',
        );
      }

      this.logger.error(
        'Could not connect to AI chat service.',
        error instanceof Error ? error.stack : undefined,
      );

      throw new ServiceUnavailableException(
        'AI chat service is currently unavailable.',
      );
    }
  }
}
