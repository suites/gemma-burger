import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { InternalServerErrorException } from '@nestjs/common';
import { ChatService } from './chat.service';
import { of, throwError } from 'rxjs';
import { Readable } from 'stream';
import { AxiosError, AxiosResponse } from 'axios';

describe('ChatService', () => {
  let service: ChatService;
  let httpService: HttpService;
  let configService: ConfigService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ChatService,
        {
          provide: HttpService,
          useValue: {
            post: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockReturnValue('http://localhost:8000/chat'),
          },
        },
      ],
    }).compile();

    service = module.get<ChatService>(ChatService);
    httpService = module.get<HttpService>(HttpService);
    configService = module.get<ConfigService>(ConfigService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('generateStream', () => {
    it('should return a readable stream on successful request', async () => {
      const mockStream = new Readable();
      mockStream.push('test response');
      mockStream.push(null);

      const mockResponse: AxiosResponse<Readable> = {
        data: mockStream,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} as any },
      };

      jest.spyOn(httpService, 'post').mockReturnValue(of(mockResponse));

      const result = await service.generateStream('Hello', 'session-123');

      expect(result).toBe(mockStream);
      expect(jest.mocked(httpService.post)).toHaveBeenCalledWith(
        'http://localhost:8000/chat',
        { message: 'Hello', session_id: 'session-123' },
        { responseType: 'stream', timeout: 30000 },
      );
    });

    it('should throw InternalServerErrorException when connection is refused', async () => {
      const error: Partial<AxiosError> = {
        code: 'ECONNREFUSED',
        message: 'Connection refused',
        name: 'AxiosError',
        config: { headers: {} as any },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      jest.spyOn(httpService, 'post').mockReturnValue(throwError(() => error));

      await expect(
        service.generateStream('Hello', 'session-123'),
      ).rejects.toThrow(InternalServerErrorException);

      await expect(
        service.generateStream('Hello', 'session-123'),
      ).rejects.toThrow(
        'AI server is not responding. Please ensure the model server is running.',
      );
    });

    it('should throw InternalServerErrorException on timeout', async () => {
      const error: Partial<AxiosError> = {
        code: 'ETIMEDOUT',
        message: 'Timeout',
        name: 'AxiosError',
        config: { headers: {} as any },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      jest.spyOn(httpService, 'post').mockReturnValue(throwError(() => error));

      await expect(
        service.generateStream('Hello', 'session-123'),
      ).rejects.toThrow(
        'AI server request timed out. The model may be overloaded.',
      );
    });

    it('should throw InternalServerErrorException on 5xx errors', async () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 500,
          data: { detail: 'Server error' },
          statusText: 'Internal Server Error',
          headers: {},
          config: { headers: {} as any },
        },
        message: 'Server error',
        name: 'AxiosError',
        config: { headers: {} as any },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      jest.spyOn(httpService, 'post').mockReturnValue(throwError(() => error));

      await expect(
        service.generateStream('Hello', 'session-123'),
      ).rejects.toThrow(
        'AI server encountered an internal error. Please try again later.',
      );
    });

    it('should throw InternalServerErrorException on 4xx errors', async () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 400,
          data: { detail: 'Bad request' },
          statusText: 'Bad Request',
          headers: {},
          config: { headers: {} as any },
        },
        message: 'Bad request',
        name: 'AxiosError',
        config: { headers: {} as any },
        isAxiosError: true,
        toJSON: () => ({}),
      };

      jest.spyOn(httpService, 'post').mockReturnValue(throwError(() => error));

      await expect(
        service.generateStream('Hello', 'session-123'),
      ).rejects.toThrow('Invalid request to AI server: Bad request');
    });

    it('should use AI_SERVER_URL from config', () => {
      expect(jest.mocked(configService.get)).toHaveBeenCalledWith(
        'AI_SERVER_URL',
        'http://localhost:8000/chat',
      );
    });
  });
});
