import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { AxiosResponse } from 'axios';
import { lastValueFrom } from 'rxjs';
import { Readable } from 'stream';

@Injectable()
export class ChatService {
  private readonly aiServerUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.aiServerUrl = this.configService.get<string>(
      'AI_SERVER_URL',
      'http://localhost:8000/chat',
    );
  }

  // 반환 타입이 문자열이 아니라 'Readable Stream'이 됩니다.
  async generateStream(
    userMessage: string,
    sessionId: string,
  ): Promise<Readable> {
    try {
      const payload = { message: userMessage, session_id: sessionId };

      const response$ = this.httpService.post(this.aiServerUrl, payload, {
        responseType: 'stream',
        timeout: 30000,
      });

      const response: AxiosResponse<Readable> = await lastValueFrom(response$);

      return response.data;
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        throw new InternalServerErrorException(
          'AI server is not responding. Please ensure the model server is running.',
        );
      }

      if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
        throw new InternalServerErrorException(
          'AI server request timed out. The model may be overloaded.',
        );
      }

      if (error.response?.status >= 500) {
        throw new InternalServerErrorException(
          'AI server encountered an internal error. Please try again later.',
        );
      }

      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw new InternalServerErrorException(
          `Invalid request to AI server: ${error.response?.data?.detail || 'Unknown error'}`,
        );
      }

      throw new InternalServerErrorException(
        'Failed to communicate with AI server. Please try again.',
      );
    }
  }
}
