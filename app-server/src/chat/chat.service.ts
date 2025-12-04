import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';

@Injectable()
export class ChatService {
  // Python AI 서버 주소 (로컬)
  private readonly aiServerUrl = 'http://localhost:8000/generate';

  constructor(private readonly httpService: HttpService) {}

  async generateReply(userMessage: string): Promise<string> {
    try {
      // 1. Python 서버로 페이로드 전송
      // (나중에 여기서 RAG로 검색된 메뉴 정보를 프롬프트에 섞을 예정입니다)
      const payload = {
        prompt: userMessage,
        max_tokens: 100,
        temperature: 0.7,
      };

      const response = await lastValueFrom(
        this.httpService.post<{ text: string }>(this.aiServerUrl, payload),
      );

      // 2. 응답 반환 ({ text: "..." })
      return response.data.text;
    } catch (error) {
      if (error instanceof Error) {
        console.error('AI Server Error:', error.message);
      }
      throw new InternalServerErrorException('AI 직원이 잠시 휴식 중입니다.');
    }
  }
}
