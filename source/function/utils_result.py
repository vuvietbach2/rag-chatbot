from source.rerank.utils_rerank import Rerank_Utils
from source.search.utils_search import Qdrant_Utils
from source.extract.utils_extract import Extract_Information
from source.core.config import Settings
from source.function.utils_shared import load_information_from_json, search_from_json, clean_code_fence_safe, parse_raw_json
from source.model.embedding_model import Sentences_Transformer_Embedding
import traceback
import time
import json # Import thêm json

class RAG():
    def __init__(self, generator_utils, bert_utils: Extract_Information, qdrant_utils: Qdrant_Utils, rerank_utils: Rerank_Utils, setting: Settings, model_embedding: Sentences_Transformer_Embedding):
         self.qdrant_utils = qdrant_utils
         self.rerank_utils = rerank_utils
         self.extract_utils = bert_utils
         self.generate = generator_utils
         self.model_embedding = model_embedding
         # Load dữ liệu xã giao từ file information.json
         self.corpus, self.corpus_embedding = load_information_from_json(setting, self.model_embedding)

    def get_Article_Content_Results(self, user_Query):
        print(f"\n{'='*30}\n🚀 [RAG START] User Query: {user_Query}")
        start_time = time.time()
        
        # --- BƯỚC 1: ROUTER AI (DÙNG FILE YAML) ---
        # Gọi hàm router_check trong DeepSeek_Generate
        check = self.generate.router_check(user_Query)
        
        if check == 0:
             print(">> [Router AI] => Luồng 0 (Xã giao/Thông tin)")
             # Tìm kiếm trong file JSON thông tin chung
             context = search_from_json(self.corpus_embedding, self.corpus, user_Query, self.model_embedding)
             return self.generate.generate_information(user_Query, context), [], False
        
        elif check == 2:
            print(">> [Router AI] => Luồng 2 (Câu hỏi rác/Không hợp lệ)")
            return "Xin lỗi, tôi chỉ hỗ trợ giải đáp các vấn đề liên quan đến Pháp luật Việt Nam.", [], False

        elif check == 1:
            try:
                print(">> [Router AI] => Luồng 1 (Tra cứu Luật)")
                
                # --- BƯỚC 2: SEARCH ---
                search_results = self.qdrant_utils.search_documents(user_Query, top_k=30)
                
                article_documents = []
                for item in search_results:
                    content = ""
                    metadata = {}
                    if hasattr(item, 'page_content'):
                        content = item.page_content
                        metadata = getattr(item, 'metadata', {})
                    elif isinstance(item, tuple):
                        content = item[0].page_content if hasattr(item[0], 'page_content') else str(item[0])
                        metadata = getattr(item[0], 'metadata', {})
                    
                    if content:
                        formatted_info = {'doc_metadata': metadata} 
                        article_documents.append((content, formatted_info))

                # --- BƯỚC 3: RERANK ---
                if not article_documents:
                    return "Xin lỗi, dữ liệu luật chưa cập nhật vấn đề này.", [], True
                
                rerank_article_documents = self.rerank_utils.rerank_documents_finetune(user_Query, article_documents)
                
                if not rerank_article_documents:
                     return "Không tìm thấy văn bản luật phù hợp.", [], True

                # --- BƯỚC 4: GENERATE (DÙNG PROMPT YAML) ---
                print(">> [Generate] Đang gọi AI (Prompt: response)...")
                
                # Chuẩn bị context dạng Dict để khớp với logic cũ hoặc list
                docs_for_ai = [doc.replace("_", " ") for doc, _ in rerank_article_documents]
                
                # Gọi DeepSeek (nó sẽ dùng prompt từ YAML)
                result_gemini = self.generate.generate_response(user_Query, docs_for_ai)
                
                # Parse kết quả JSON (YAML quy định trả về key 'answer' và 'key')
                answer_result = clean_code_fence_safe(result_gemini)
                answer_result_json = parse_raw_json(answer_result)
                
                final_answer = answer_result_json.get('answer', str(answer_result_json))
                
                # --- BƯỚC 5: TẠO TRÍCH DẪN (NÚT XANH) ---
                # Chúng ta lấy trực tiếp từ rerank docs để đảm bảo luôn hiện
                lst_Article_Quote = []
                for i, (doc, infor) in enumerate(rerank_article_documents):
                    meta = infor.get('doc_metadata', {}) if 'doc_metadata' in infor else infor
                    quote = f"""\
                    Tài liệu tham khảo: {i+1}
                    Loại văn bản: {meta.get("LoaiVanBan", "Văn bản pháp luật")}
                    Số hiệu: {meta.get("SoHieu", "VN-LAW")}
                    Ngày ban hành: {meta.get("NgayBanHanh", "")}
                    Trích yếu: {meta.get("Article", "")}
                    <=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>
                    {doc.replace("_", " ").replace(' .', '.').replace(' ,', ',')}
                    """
                    lst_Article_Quote.append("\n".join([line.strip() for line in quote.split('\n')]))
                
                # Logic Web Search fallback
                keywords_no_info = ["xin lỗi", "không tìm thấy", "chưa cập nhật", "ngoài phạm vi"]
                use_web_search = False
                if any(k in final_answer.lower() for k in keywords_no_info) and not lst_Article_Quote:
                    use_web_search = True

                return final_answer, lst_Article_Quote, use_web_search

            except Exception as e:
                print(f"❌ [ERROR] Lỗi RAG: {str(e)}")
                traceback.print_exc()
                return "Hệ thống gặp sự cố. Đang chuyển sang tìm kiếm Internet...", [], True
        
        else:
            return "Xin lỗi, tôi chưa hiểu ý định của bạn.", [], False