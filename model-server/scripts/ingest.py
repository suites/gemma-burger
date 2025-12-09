import sys
import os
import json
from langchain_core.documents import Document

# 상위 디렉토리(app) 모듈 import 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.rag import rag_engine

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: File not found at {filepath}")
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def ingest():
    base_path = os.path.dirname(__file__)
    menu_path = os.path.join(base_path, '../../resources/menu.json')
    info_path = os.path.join(base_path, '../../resources/store_info.json')
    
    docs = []

    # 1. 메뉴 데이터 처리 (Type: menu)
    print(f"🍔 Loading Menu Data from: {menu_path}")
    menu_data = load_json(menu_path)
    
    for item in menu_data:
        content = f"Menu Item: {item['name']}\nDescription: {item['description']}\nPrice: ${item['price']}\nCategory: {item['category']}"
        
        # 메타데이터에 type='menu' 강제 주입
        metadata = item.copy()
        metadata["type"] = "menu"
        
        docs.append(Document(page_content=content, metadata=metadata))

    # 2. 매장 정보 데이터 처리 (Type: info)
    print(f"ℹ️ Loading Store Info from: {info_path}")
    info_data = load_json(info_path)
    
    for item in info_data:
        content = f"[{item['category']}] {item['content']}"
        
        # store_info.json에는 이미 type='info'가 들어있지만 확실하게 처리
        metadata = item.copy()
        if "type" not in metadata:
            metadata["type"] = "info"
            
        docs.append(Document(page_content=content, metadata=metadata))

    # 3. Pinecone 업로드
    if docs:
        print(f"🚀 Uploading {len(docs)} documents to Pinecone...")
        # (선택사항) 기존 데이터 삭제 후 재생성하려면:
        # rag_engine.vector_store.delete(delete_all=True)
        
        rag_engine.vector_store.add_documents(docs)
        print("✅ Ingestion Complete!")
    else:
        print("❌ No documents to upload.")

if __name__ == "__main__":
    ingest()