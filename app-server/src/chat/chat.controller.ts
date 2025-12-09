import { Controller, Post, Body, Res } from '@nestjs/common';
import { ChatService } from './chat.service';
import { Response } from 'express';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  async chat(
    @Body('message') message: string,
    @Body('sessionId') sessionId: string,
    @Res() res: Response,
  ) {
    // 1. 서비스로부터 스트림 획득
    const stream = await this.chatService.generateStream(message, sessionId);

    // 2. 헤더 설정 (SSE 표준)
    res.setHeader('Content-Type', 'text/plain'); // 단순 텍스트 스트림
    res.setHeader('Transfer-Encoding', 'chunked'); // 청크 단위 전송

    // 3. 파이프 연결 (Python Stream -> NestJS Response -> Browser)
    stream.pipe(res);
  }
}
