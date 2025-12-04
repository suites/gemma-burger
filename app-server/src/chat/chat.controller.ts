import { Controller, Post, Body } from '@nestjs/common';
import { ChatService } from './chat.service';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  async chat(@Body('message') message: string) {
    // 1. 사용자의 메시지를 받아 AI에게 전달
    const aiResponse = await this.chatService.generateReply(message);

    // 2. 클라이언트에게 응답
    return { reply: aiResponse };
  }
}
