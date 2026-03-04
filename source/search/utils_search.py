from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from pyvi import ViTokenizer
from typing import Optional
from source.generate.generate import Gemini_Generate
from source.data.vectordb.qdrant import Qdrant_Vector
from source.function.utils_shared import extract_json_dict

class Qdrant_Utils():
    def __init__(self, qdrant: Qdrant_Vector, gemini_util: Gemini_Generate):
        self.qdrant = qdrant
        self.gemini = gemini_util

    def search_documents(self, query, top_k=25, filter: Optional[Filter] = None):
        # Mở kết nối (trả về Langchain Wrapper)
        connection = self.qdrant.Open_Qdrant()
        
        # Lưu ý: Langchain Qdrant wrapper nhận tham số filter là qdrant_client.models.Filter
        search_results = connection.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filter  # Truyền trực tiếp object Filter của qdrant-client
        )
        return search_results

    def build_metadata_filter(self, entity_dict: dict) -> Optional[Filter]:
        if not entity_dict:
            return None
            
        conditions = []
        for key, value in entity_dict.items():
            # Bỏ qua nếu giá trị rỗng
            if not value:
                continue
                
            # Chuẩn hóa key để khớp với metadata trong DB
            # Ví dụ: NgayBanHanhFilter -> metadata.NgayBanHanhFilter
            # Tuy nhiên, trong file ingest, metadata là phẳng.
            # Hãy kiểm tra lại tên trường trong DB. Giả sử là đúng như key.
            
            # LƯU Ý QUAN TRỌNG: Qdrant yêu cầu đường dẫn key trong payload
            # Nếu bạn lưu metadata là một dict con trong payload (ví dụ: payload.metadata.LoaiVanBan)
            # thì key phải là "metadata.LoaiVanBan".
            # Nếu metadata nằm thẳng ở root của payload, thì key là "LoaiVanBan".
            # Dựa trên file ingest trước đó: doc = Document(page_content=..., metadata=metadata)
            # Langchain sẽ lưu metadata vào key "metadata".
            
            db_key = f"metadata.{key}" 

            if key == "NgayBanHanhFilter":
                # MatchAny cho phép tìm một trong các giá trị (nếu value là list)
                # Nếu value là string đơn, chuyển thành list
                val_list = value if isinstance(value, list) else [value]
                conditions.append(
                    FieldCondition(
                        key=db_key,
                        match=MatchAny(any=val_list)
                    )
                )
            else:
                # MatchValue cho giá trị chính xác
                conditions.append(
                    FieldCondition(
                        key=db_key,
                        match=MatchValue(value=value) # Bỏ .lower() nếu DB lưu có hoa thường
                    )
                )
        
        if not conditions:
            return None
            
        return Filter(must=conditions) # Dùng 'must' để bắt buộc thỏa mãn (AND logic)

    def search_With_Similarity_Queries(self, user_query: str):
        # 1. Sinh câu hỏi phụ
        queries = self.gemini.generate_query(user_query)
        query_results = []
        
        print(f"   -> Generated {len(queries)} queries: {queries}")

        for i, query in enumerate(queries):
            # 2. Tokenize tiếng Việt
            tokenized_query = ViTokenizer.tokenize(query)
            
            # 3. Trích xuất thực thể để lọc
            try:
                raw_result = self.gemini.extract_entities(query)
                entity_dict = extract_json_dict(raw_result)
                print(f"      - Query {i+1} Entities: {entity_dict}")
                metadata_filter = self.build_metadata_filter(entity_dict)
            except Exception as e:
                print(f"      ⚠️ Lỗi trích xuất entity: {e}")
                metadata_filter = None

            # 4. Tìm kiếm
            try:
                search_results = self.search_documents(tokenized_query, filter=metadata_filter)
                query_results.append(search_results)
            except Exception as e:
                print(f"      ❌ Lỗi Search Qdrant (Query {i}): {e}")
                # Fallback: Tìm không cần filter nếu filter lỗi
                if metadata_filter:
                    print("         -> Thử lại không dùng Filter...")
                    search_results = self.search_documents(tokenized_query, filter=None)
                    query_results.append(search_results)

        return query_results