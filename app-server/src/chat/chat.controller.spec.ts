import { Test, TestingModule } from '@nestjs/testing';
import { ChatController } from './chat.controller';
import { ChatService } from './chat.service';
import { Response } from 'express';
import { Readable } from 'stream';

describe('ChatController', () => {
  let controller: ChatController;
  let chatService: ChatService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [ChatController],
      providers: [
        {
          provide: ChatService,
          useValue: {
            generateStream: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get<ChatController>(ChatController);
    chatService = module.get<ChatService>(ChatService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('chat', () => {
    it('should stream response from chatService', async () => {
      const mockStream = new Readable();
      mockStream.push('AI response');
      mockStream.push(null);

      jest.spyOn(chatService, 'generateStream').mockResolvedValue(mockStream);

      const mockResponse = {
        setHeader: jest.fn(),
      } as unknown as Response;

      const pipeSpy = jest
        .spyOn(mockStream, 'pipe')
        .mockReturnValue(mockResponse as never);

      await controller.chat('Hello', 'session-123', mockResponse);

      expect(jest.mocked(chatService.generateStream)).toHaveBeenCalledWith(
        'Hello',
        'session-123',
      );
      expect(jest.mocked(mockResponse.setHeader)).toHaveBeenNthCalledWith(
        1,
        'Content-Type',
        'text/plain',
      );
      expect(jest.mocked(mockResponse.setHeader)).toHaveBeenNthCalledWith(
        2,
        'Transfer-Encoding',
        'chunked',
      );
      expect(pipeSpy).toHaveBeenCalledWith(mockResponse);
    });

    it('should handle service errors', async () => {
      jest
        .spyOn(chatService, 'generateStream')
        .mockRejectedValue(new Error('Service error'));

      const mockResponse = {
        setHeader: jest.fn(),
      } as unknown as Response;

      await expect(
        controller.chat('Hello', 'session-123', mockResponse),
      ).rejects.toThrow('Service error');
    });
  });
});
