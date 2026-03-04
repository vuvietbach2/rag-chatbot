from source.core.config import Settings
from source.model.embedding_model import Sentences_Transformer_Embedding
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient  # Thêm thư viện này

class Qdrant_Vector():
    def __init__(self, setting: Settings, embedding: Sentences_Transformer_Embedding):
        self.setting = setting
        self.embedding = embedding

    def Open_Qdrant(self):
        # 1. Tạo Client kết nối thủ công (Giống file ingest)
        client = QdrantClient(
            url=self.setting.URL_QDRANT_LOCAL,
            prefer_grpc=False 
        )

        # 2. Khởi tạo Langchain Qdrant Wrapper bằng client đã tạo
        open_collection = Qdrant(
            client=client,
            collection_name=self.setting.EXIST_COLLECTION_NAME,
            embeddings=self.embedding.embeddings_bkai,
            metadata_payload_key=self.setting.metadata_payload_key
        )
        
        return open_collection