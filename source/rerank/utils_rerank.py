from typing import List,Tuple
from source.model.rerank_model import Cohere
from cohere import ClientV2
from source.model.rerank_model_finetune import RerankModelFinetune

class Rerank_Utils():

    def __init__(self,model_rerank:Cohere, model_finetune:RerankModelFinetune):
         self.model_rerank=model_rerank
         self.model_finetune = model_finetune.model
    
    def reciprocal_rank_fusion(self,documents_nested, k=60):
        document_scores = {}  
        try:
            for query_idx, result_list in enumerate(documents_nested):
                for rank, (doc, _) in enumerate(result_list):
                    doc_key = doc.page_content
                    doc_metadata=doc.metadata
                    rrf_score = 1 / (k + rank + 1)
                    if doc_key not in document_scores:
                        document_scores[doc_key] = {
                            "score": 0,
                            "doc_metadata":doc_metadata,
                            "count": 0  
                        }
                    document_scores[doc_key]["score"] += rrf_score
                    document_scores[doc_key]["count"] += 1
            reranked_docs = sorted(document_scores.items(), key=lambda x: x[1]["score"], reverse=True)
            
            # # In thông tin chi tiết về kết quả đã xếp hạng
            # print("\n=== Kết quả đã xếp hạng lại ===")
            # print(f"Tổng số kết quả: {len(reranked_docs)}")
            # for idx, (content, info) in enumerate(reranked_docs[:50], 1):
            #     print(f"\n--- Kết quả #{idx} ---")
            #     print(f"Điểm số: {info['score']:.4f}")
            #     print(f"Số lần xuất hiện: {info['count']}")
            #     print(f"Nội dung: {content[:200]}...")  # In 200 ký tự đầu tiên
                
            return reranked_docs[:50]  
        except Exception as e:
            print(f"Lỗi khi tính RRF: {e}")
            return []
    
    def rerank_documents(self,query,documents) -> List[Tuple[str, float]]:
        # print("Đang sử dụng mô hình Cohere để xếp hạng lại tài liệu.")
        doc_contents = [(doc).replace("_"," ").replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?').replace(' :', ':').replace(' ;', ';') for doc,_ in documents]
        try:
            co = ClientV2(self.model_rerank.key_manager.get_next_key())
            response = co.rerank(
                model=self.model_rerank.model_cohere,
                query=query,
                documents=doc_contents,
                top_n=5,
            )
            reranked_results = response.results
            # print("\n=== Kết quả từ Cohere Rerank ===")
            # for idx, result in enumerate(reranked_results, 1):
            #     print(f"\n--- Kết quả #{idx} ---")
            #     print(f"Điểm số: {result.relevance_score:.4f}")
            #     print(f"Index: {result.index}")
            #     print(f"Nội dung: {doc_contents[result.index][:200]}...")
            
            ranked_documents = [documents[res.index] for res in reranked_results]
            
            # print("\n=== Kết quả cuối cùng sau khi xếp hạng ===")
            # for idx, (doc, score) in enumerate(ranked_documents, 1):
            #     print(f"\n--- Kết quả #{idx} ---")
            #     print(f"Điểm số: {score}")
            #     print(f"Nội dung: {doc[:200]}...")
            
        except Exception as e:
            print(f"An error occurred: {e}")
        return ranked_documents  
    
    def rerank_documents_finetune(self,query,documents) -> List[Tuple[str, float]]:
        if len(documents) > 50:
            raise ValueError("Số lượng documents không được vượt quá 50.")
            
        doc_contents = [doc for doc, _ in documents]
        doc_metadata = [info['doc_metadata'] for _, info in documents]
        doc_contents = [(doc).replace("_"," ").replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?').replace(' :', ':').replace(' ;', ';') for doc in doc_contents]
        try:
            pairs = [(query, doc) for doc in doc_contents]
            scores = self.model_finetune.predict(pairs)
            scores = [float(score) for score in scores]
            ranked = sorted(zip(scores, range(len(doc_contents))), key=lambda x: x[0], reverse=True)
            return [(doc_contents[idx], {'score': score, 'doc_metadata': doc_metadata[idx]}) for score, idx in ranked[:5]]
        except Exception as e:
            print(f"An error occurred: {e}")
            return []  