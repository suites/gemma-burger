import { Controller, Post, Body, Res } from '@nestjs/common';
import { ChatService } from './chat.service';
import { Response } from 'express';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  // 채팅 엔드포인트
  @Post()
  async chat(
    @Body('message') message: string,
    @Body('sessionId') sessionId: string,
    @Res() res: Response,
  ) {
    const stream = await this.chatService.generateStream(message, sessionId);
    res.setHeader('Content-Type', 'text/plain');
    res.setHeader('Transfer-Encoding', 'chunked');
    stream.pipe(res);
  }

  // Sara와 Rosy의 무한 시뮬레이션 엔드포인트
  @Post('simulate')
  async simulate(@Body('sessionId') sessionId: string, @Res() res: Response) {
    // 1. 서비스로부터 시뮬레이션 스트림 획득 (Python /chat/simulate 호출)
    const stream = await this.chatService.startSimulation(sessionId);

    // 2. 헤더 설정
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Transfer-Encoding', 'chunked');

    // 3. 파이프 연결 (Python Simulation Stream -> NestJS -> Browser)
    stream.pipe(res);
  }
}
