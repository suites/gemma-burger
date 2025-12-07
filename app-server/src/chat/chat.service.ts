// app-server/src/chat/chat.service.ts
import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';

@Injectable()
export class ChatService {
  // Python 서버의 새로운 통합 엔드포인트
  private readonly aiServerUrl = 'http://localhost:8000/chat';

  constructor(private readonly httpService: HttpService) {}

  async generateReply(userMessage: string): Promise<string> {
    try {
      // Python 서버 스펙에 맞춘 페이로드
      const payload = {
        message: userMessage,
      };

      const { data } = await lastValueFrom(
        this.httpService.post(this.aiServerUrl, payload),
      );

      // 응답 필드: { reply: "..." }
      return data.reply;
    } catch (error) {
      console.error('AI Server Error:', error.message);
      throw new InternalServerErrorException(
        'Sorry, I cannot connect to the AI kitchen right now. 😢',
      );
    }
  }
}
