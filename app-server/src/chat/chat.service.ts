// src/chat/chat.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';
import { RagService } from '../rag/rag.service'; // ⬅️ Import

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);
  private readonly aiServerUrl = 'http://localhost:8000/generate';

  constructor(
    private readonly httpService: HttpService,
    private readonly ragService: RagService, // ⬅️ 주입
  ) {}

  async generateReply(userMessage: string): Promise<string> {
    // 1. [Retrieval] 사용자 질문과 관련된 메뉴 검색
    const docs = await this.ragService.search(userMessage);

    // 검색된 문서 내용을 하나의 문자열로 합침 (Context)
    const context = docs.map((d) => d.pageContent).join('\n---\n');
    this.logger.debug(`🔍 RAG Context:\n${context}`);

    // 2. [Prompting] 시스템 페르소나 + 지식 + 질문 결합
    const systemPrompt = `
You are Gemma, a friendly AI staff at Gemma Burger.
Answer the customer's question based ONLY on the menu information below.

[Menu Information]
${context}

[Instructions]
- Recommend items from the menu.
- If the item is not in the menu, apologize and suggest something else.
- Use emojis.

Customer: ${userMessage}
Answer:
    `.trim();

    // 3. [Generation] Python AI 서버로 요청
    try {
      const payload = {
        prompt: systemPrompt,
        max_tokens: 300,
        temperature: 0.7,
      };

      const { data } = await lastValueFrom(
        this.httpService.post(this.aiServerUrl, payload),
      );

      return data.text;
    } catch (error) {
      this.logger.error('AI Server Error', error);
      return "Sorry, I'm having trouble connecting to the kitchen.";
    }
  }
}
