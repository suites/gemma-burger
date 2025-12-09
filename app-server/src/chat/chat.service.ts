import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { AxiosResponse } from 'axios';
import { lastValueFrom } from 'rxjs';
import { Readable } from 'stream';

@Injectable()
export class ChatService {
  private readonly aiServerUrl = 'http://localhost:8000/chat';

  constructor(private readonly httpService: HttpService) {}

  // 반환 타입이 문자열이 아니라 'Readable Stream'이 됩니다.
  async generateStream(
    userMessage: string,
    sessionId: string,
  ): Promise<Readable> {
    try {
      const payload = { message: userMessage, session_id: sessionId };

      // 1. Python 서버에 요청 (responseType: 'stream' 필수!)
      const response$ = this.httpService.post(this.aiServerUrl, payload, {
        responseType: 'stream',
      });

      const response: AxiosResponse<Readable> = await lastValueFrom(response$);

      // 2. Python에서 받은 스트림 객체 반환
      return response.data;
    } catch (error) {
      console.error('AI Server Error:', error.message);
      throw new InternalServerErrorException('AI 연결 실패');
    }
  }
}
