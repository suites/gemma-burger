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

  async startSimulation(sessionId: string): Promise<Readable> {
    try {
      // 1. 시뮬레이션 전용 엔드포인트 URL 설정
      const simulateUrl = `${this.aiServerUrl}/simulate`;

      // 2. 페이로드 설정 (메시지 없이 세션 ID만 전송)
      const payload = { session_id: sessionId };

      // 3. Python 서버에 스트림 요청
      const response$ = this.httpService.post(simulateUrl, payload, {
        responseType: 'stream',
      });

      const response: AxiosResponse<Readable> = await lastValueFrom(response$);

      // 4. 시뮬레이션 스트림 객체 반환
      return response.data;
    } catch (error) {
      console.error('Simulation Connection Error:', error.message);
      throw new InternalServerErrorException('시뮬레이션 서버 연결 실패');
    }
  }
}
