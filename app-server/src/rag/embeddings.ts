import { Embeddings, EmbeddingsParams } from '@langchain/core/embeddings';
import { pipeline, FeatureExtractionPipeline } from '@huggingface/transformers';

/**
 * @huggingface/transformers (v3)를 사용하는 커스텀 임베딩 클래스
 * LangChain의 Embeddings 추상 클래스를 구현하여 호환성을 확보합니다.
 */
export class LocalHuggingFaceEmbeddings extends Embeddings {
  private model: string;
  private pipe: FeatureExtractionPipeline | null = null;

  constructor(fields?: EmbeddingsParams & { model?: string }) {
    super(fields ?? {});
    // 기본 모델: 작고 빠르며 성능이 검증된 all-MiniLM-L6-v2 사용
    this.model = fields?.model ?? 'Xenova/all-MiniLM-L6-v2';
  }

  /**
   * 파이프라인이 초기화되지 않았다면 로드합니다. (Lazy Loading)
   */
  async ensurePipeline() {
    if (!this.pipe) {
      console.log(`🔧 Initializing local embedding pipeline: ${this.model}`);
      const pipe = await pipeline('feature-extraction', this.model);
      this.pipe = pipe;
    }
  }

  /**
   * 문서 배열(Documents)을 벡터 배열로 변환
   */
  async embedDocuments(documents: string[]): Promise<number[][]> {
    await this.ensurePipeline();
    const embeddings: number[][] = [];

    for (const doc of documents) {
      // pooling: 'mean' -> 단어 벡터들의 평균을 구해 문장 전체 벡터 생성
      // normalize: true -> 코사인 유사도 계산을 위해 정규화
      const output = await this.pipe!(doc, {
        pooling: 'mean',
        normalize: true,
      });

      // Tensor 데이터를 일반 배열로 변환하여 저장
      embeddings.push(Array.from(output.data));
    }
    return embeddings;
  }

  /**
   * 검색어(Query)를 벡터로 변환
   */
  async embedQuery(document: string): Promise<number[]> {
    await this.ensurePipeline();
    const output = await this.pipe!(document, {
      pooling: 'mean',
      normalize: true,
    });
    return Array.from(output.data);
  }
}
