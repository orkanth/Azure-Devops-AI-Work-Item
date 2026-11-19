
import { Body, Controller, Post } from '@nestjs/common';

import { ChatRequestDto } from './dto/chat-request.dto';
import { ChatResponse, ChatService } from './chat.service';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  sendMessage(@Body() dto: ChatRequestDto): Promise<ChatResponse> {
    return this.chatService.sendMessage(dto);
  }
}
