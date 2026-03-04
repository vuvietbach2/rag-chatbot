import json
import os
import glob
from typing import List
from tqdm import tqdm

from source.core.config import Settings
from source.model.embedding_model import Sentences_Transformer_Embedding
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_core.documents import Document
from langchain_qdrant import Qdrant

def load_json_data(file_path: str) -> List[Document]:
    """Đọc file JSON với cấu trúc đặc thù (SemanticChunk-Content)"""
    filename = os.path.basename(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        raw_items = []
        
        # --- 1. Xác định cấu trúc JSON ---
        if isinstance(data, list):
            raw_items = data
        elif isinstance(data, dict):
            # Nếu là dict dạng { "0": {...}, "1": {...} }
            raw_items = list(data.values())
        
        documents = []
        valid_count = 0
        
        # --- 2. Trích xuất dữ liệu (Đã sửa cho Key của bạn) ---
        for item in raw_items:
            if not isinstance(item, dict):
                continue
                
            # Ưu tiên tìm key "SemanticChunk-Content" trước
            content = item.get("SemanticChunk-Content") or \
                      item.get("page_content") or \
                      item.get("content") or \
                      item.get("text")
            
            # Xử lý Metadata
            if "metadata" in item:
                metadata = item["metadata"]
            else:
                # Nếu không có key 'metadata' riêng, dùng chính các trường còn lại làm metadata
                metadata = item.copy()
                # Xóa content khỏi metadata để tiết kiệm bộ nhớ
                keys_to_remove = ["SemanticChunk-Content", "page_content", "content", "text"]
                for k in keys_to_remove:
                    if k in metadata:
                        del metadata[k]
            
            if content:
                # Chuyển đổi content sang string nếu cần
                if not isinstance(content, str):
                    content = str(content)
                    
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
                valid_count += 1
        
        if valid_count == 0:
            print(f"⚠️  Cảnh báo: Không tìm thấy nội dung trong file '{filename}'")
            if raw_items:
                print(f"   -> Các keys hiện có: {list(raw_items[0].keys())}")
                
        return documents

    except Exception as e:
        print(f"❌ Lỗi đọc file '{filename}': {e}")
        return []

def ingest_to_qdrant():
    print("\n" + "="*60)
    print("🚀  BẮT ĐẦU QUÁ TRÌNH NẠP DỮ LIỆU (FIXED FOR YOUR DATA)")
    print("="*60)
    
    setting = Settings()
    print(f"🔌 URL Qdrant: {setting.URL_QDRANT_LOCAL}")
    print(f"📚 Collection: {setting.EXIST_COLLECTION_NAME}")
    
    # 1. Load Model
    try:
        print("⏳ Đang tải Model Embedding...")
        embedding_model = Sentences_Transformer_Embedding(setting)
    except Exception as e:
        print(f"❌ Lỗi tải Model: {e}")
        return

    # 2. Quét File
    data_folder = "data_source"
    json_files = glob.glob(os.path.join(data_folder, "handled_*.json"))
    
    if not json_files:
        print(f"⚠️ Không tìm thấy file trong '{data_folder}'")
        return

    print(f"\n📂 Đang xử lý {len(json_files)} file:")
    all_documents = []
    
    for f in json_files:
        docs = load_json_data(f)
        if docs:
            print(f"   ✅ {os.path.basename(f)}: Lấy được {len(docs)} đoạn.")
            all_documents.extend(docs)
        else:
            print(f"   ❌ {os.path.basename(f)}: 0 đoạn.")
    
    total_docs = len(all_documents)
    print(f"\n📊 TỔNG CỘNG: {total_docs} vector cần nạp.")

    if total_docs == 0:
        print("🛑 Dừng chương trình vì không có dữ liệu.")
        return

    # 3. Đẩy vào Qdrant
    client = QdrantClient(url=setting.URL_QDRANT_LOCAL)
    
    # Lấy vector size chuẩn
    test_vec = embedding_model.embeddings_bkai.embed_query("test")
    vector_size = len(test_vec)
    
    print(f"\n🔥 Đang TÁI TẠO Collection '{setting.EXIST_COLLECTION_NAME}' (Size: {vector_size})...")
    client.recreate_collection(
        collection_name=setting.EXIST_COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=vector_size, 
            distance=models.Distance.COSINE
        )
    )

    print(f"🚀 Đang Vector hóa và nạp dữ liệu (Batching 64)...")
    
    qdrant = Qdrant(
        client=client,
        collection_name=setting.EXIST_COLLECTION_NAME,
        embeddings=embedding_model.embeddings_bkai,
    )
    
    batch_size = 64
    for i in tqdm(range(0, total_docs, batch_size), desc="Tiến độ"):
        batch = all_documents[i : i + batch_size]
        if batch:
            qdrant.add_documents(batch)
    
    print("\n" + "="*60)
    print("✅  HOÀN TẤT! HỆ THỐNG SẴN SÀNG HOẠT ĐỘNG.")
    print("="*60)

if __name__ == "__main__":
    ingest_to_qdrant()