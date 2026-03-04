from source.model.reset_apikey import APIKeyManager
from source.core.config import Settings
from sentence_transformers import CrossEncoder
class Cohere():
    def __init__(self,setting:Settings) :
        self.key_manager=APIKeyManager(setting.API_RERANKER)
        self.model_cohere=setting.MODEL_RERANK
    # def __init__(self,setting:Settings):
    #     self.rerank=CrossEncoder(setting.RERANK, trust_remote_code=True)