// src/rag/rag.service.ts
import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { Pinecone as PineconeClient } from '@pinecone-database/pinecone';
import { PineconeStore } from '@langchain/pinecone';
import { Document } from '@langchain/core/documents';
import * as fs from 'fs';
import * as path from 'path';
// 🟢 우리가 만든 커스텀 임베딩 클래스 import
import { LocalHuggingFaceEmbeddings } from './embeddings';

@Injectable()
export class RagService implements OnModuleInit {
  private readonly logger = new Logger(RagService.name);
  private vectorStore: PineconeStore;
  private embeddings: LocalHuggingFaceEmbeddings;

  constructor() {
    // 1. 커스텀 임베딩 초기화
    this.embeddings = new LocalHuggingFaceEmbeddings({
      model: 'Xenova/all-MiniLM-L6-v2',
    });
  }

  async onModuleInit() {
    // 2. Pinecone 클라이언트 연결
    const pinecone = new PineconeClient({
      apiKey: process.env.PINECONE_API_KEY,
    });
    const pineconeIndex = pinecone.Index(process.env.PINECONE_INDEX);

    // 3. LangChain VectorStore 연결 (임베딩 모델 + Pinecone 인덱스 결합)
    this.vectorStore = await PineconeStore.fromExistingIndex(this.embeddings, {
      pineconeIndex,
    });

    // 4. 데이터 주입 실행 (최초 1회만 실행 후 주석 처리 권장)
    this.ingestMenuData();
  }

  /**
   * [ETL] 메뉴 데이터(JSON) -> Document -> Vector -> Pinecone
   */
  ingestMenuData() {
    // 경로: app-server/../../data/menu.json
    const menuPath = path.join(process.cwd(), '..', 'data', 'menu.json');

    if (!fs.existsSync(menuPath)) {
      this.logger.warn(`⚠️ 메뉴 파일을 찾을 수 없습니다: ${menuPath}`);
      return;
    }

    this.logger.log('🍔 메뉴 데이터 로딩 및 벡터화 시작...');
    const menuData = JSON.parse(fs.readFileSync(menuPath, 'utf-8'));

    // LangChain Document 객체로 변환
    const docs = menuData.map((item) => {
      return new Document({
        // AI가 읽고 이해할 핵심 텍스트
        pageContent: `Menu: ${item.name}\nDesc: ${item.description}\nPrice: $${item.price}\nCategory: ${item.category}`,
        // 필터링용 메타데이터
        metadata: {
          name: item.name,
          category: item.category,
        },
      });
    });

    // ⚠️ 주의: 중복 방지 로직이 없으므로, 데이터가 이미 있다면 이 줄을 주석 처리하세요.
    // await this.vectorStore.addDocuments(docs);

    this.logger.log(
      `✅ ${docs.length}개의 메뉴 데이터가 Pinecone에 준비되었습니다.`,
    );
  }

  /**
   * [Retrieval] 사용자 질문과 유사한 메뉴 검색
   */
  async search(query: string, k = 3): Promise<Document[]> {
    return await this.vectorStore.similaritySearch(query, k);
  }
}
