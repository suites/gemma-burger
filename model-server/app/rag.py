import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

# 환경변수 로드
load_dotenv()


class RagEngine:
    def __init__(self):
        print("🔧 Initializing RAG Engine...")

        # 1. 임베딩 모델 로드 (로컬 CPU 사용, 무료/빠름)
        # model_name="sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 2. Pinecone 연결 설정
        self.index_name = os.getenv("PINECONE_INDEX_NAME")

        # 3. VectorStore 초기화 (연결만 해둠)
        # 실제 데이터 조회 시 이 객체를 사용합니다.
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name, embedding=self.embeddings
        )
        print(f"✅ RAG Engine Ready (Index: {self.index_name})")

    def search(self, query: str, k: int = 3, filter: dict = None):
        """
        질문(query)과 관련된 문서 k개를 찾아서 반환
        filter 옵션을 통해 메타데이터 필터링 지원 (예: {"type": "menu"})
        """
        print(f"🔍 [RAG] Searching for: '{query}' (Filter: {filter})")
        # similarity_search: 가장 유사한 문서 검색
        docs = self.vector_store.similarity_search(query, k=k, filter=filter)
        # 텍스트 내용만 리스트로 반환
        return [doc.page_content for doc in docs]


# 싱글톤 인스턴스 생성
rag_engine = RagEngine()
