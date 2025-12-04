import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';

@Injectable()
export class ChatService {
  // 🔴 수정 전: http://localhost:8000/generate
  // 🟢 수정 후: Python 서버의 새로운 통합 엔드포인트
  private readonly aiServerUrl = 'http://localhost:8000/chat';

  constructor(private readonly httpService: HttpService) {}

  async generateReply(userMessage: string): Promise<string> {
    try {
      // 1. Python 서버로 요청 전송
      // 이제 복잡한 프롬프트 조립은 Python이 다 하므로,
      // NestJS는 사용자의 메시지만 깔끔하게 넘기면 됩니다.
      const payload = {
        message: userMessage, // ⬅️ Python의 ChatRequest 모델과 일치해야 함
      };

      const { data } = await lastValueFrom(
        this.httpService.post(this.aiServerUrl, payload),
      );

      // 2. 응답 반환 ({ reply: "..." })
      return data.reply;
    } catch (error) {
      console.error('AI Server Error:', error.message);
      throw new InternalServerErrorException(
        'AI 직원이 잠시 휴식 중입니다. (AI Server Connection Error)',
      );
    }
  }
}
