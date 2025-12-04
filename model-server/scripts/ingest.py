# model-server/scripts/ingest.py
import json
import os
import sys

from langchain_core.documents import Document

# [Setup] 상위 디렉토리(app)를 import 할 수 있게 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.rag import rag_engine


def ingest():
    # 1. 메뉴 데이터 파일 경로 찾기
    # model-server/scripts/../../data/menu.json
    base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, "../../data/menu.json")

    print(f"📂 Loading data from: {os.path.abspath(data_path)}")

    if not os.path.exists(data_path):
        print("❌ Error: menu.json not found!")
        return

    with open(data_path, "r") as f:
        menu_data = json.load(f)

    # 2. Document 객체로 변환
    docs = []
    for item in menu_data:
        # 검색이 잘 되도록 텍스트를 풍부하게 구성
        content = f"Menu Item: {item['name']}\nDescription: {item['description']}\nPrice: ${item['price']}\nCategory: {item['category']}"

        docs.append(
            Document(
                page_content=content,
                metadata={
                    "name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                },
            )
        )

    # 3. Pinecone에 업로드
    print(f"🚀 Uploading {len(docs)} documents to Pinecone...")
    rag_engine.vector_store.add_documents(docs)
    print("✅ Ingestion Complete!")


if __name__ == "__main__":
    ingest()
