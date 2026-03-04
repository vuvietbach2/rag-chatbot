from fastapi import APIRouter, HTTPException
from source.function.utils_result import RAG
from source.search.utils_search import Qdrant_Utils
from source.rerank.utils_rerank import Rerank_Utils  
from source.model.embedding_model import Sentences_Transformer_Embedding
from source.model.extract_model import Bert_Extract
from source.model.generate_model import Gemini
from source.model.rerank_model import Cohere
from source.model.rerank_model_finetune import RerankModelFinetune
from source.data.vectordb.qdrant import Qdrant_Vector
from source.core.config import Settings

# Import DeepSeek
from source.generate.deepseek_generate import DeepSeek_Generate 

from source.extract.utils_extract import Extract_Information
from source.schema.chatbot_querry import ChatbotQuery
from source.tool.utils_search import Utils_Search_Tools
from source.tool.google_search import GoogleSearchTool

setting = Settings()
cohere = Cohere(setting)
bert = Bert_Extract(setting)
sentences_transformer_embedding = Sentences_Transformer_Embedding(setting)
qdrant = Qdrant_Vector(setting, sentences_transformer_embedding)

router = APIRouter()
model_finetune = RerankModelFinetune(setting)
rerank_Utils = Rerank_Utils(cohere, model_finetune)
extract_Utils = Extract_Information(bert)

# Khởi tạo DeepSeek
generate_Utils = DeepSeek_Generate(setting)

# Các Utils khác
qdrant_Utils = Qdrant_Utils(qdrant, generate_Utils)
rag = RAG(generate_Utils, extract_Utils, qdrant_Utils, rerank_Utils, setting, sentences_transformer_embedding)

# Khởi tạo công cụ tìm kiếm Web
google_search_tools = GoogleSearchTool(setting)
search_tools = Utils_Search_Tools(setting, generate_Utils, extract_Utils, google_search_tools)

# ==============================================================================
# 1. ENDPOINT SEARCH WEB (ĐÃ SỬA LỖI CRASH KHI CHÀO HỎI)
# ==============================================================================
@router.post("/chatbot-with-search-web")
def chatbot_with_search_web(query: ChatbotQuery):
    try:
        user_input = query.query.strip()
        
        # --- 🛡️ BỘ LỌC CHỐNG CRASH ---
        # Nếu là câu xã giao, TRẢ LỜI LUÔN, KHÔNG GỌI GOOGLE SEARCH (Tránh lỗi 500)
        social_keywords = ["xin chào", "chào bạn", "hello", "hi", "bạn là ai", "tên gì", "giúp gì"]
        # Điều kiện: Có từ khóa xã giao HOẶC câu quá ngắn (dưới 3 từ)
        if any(k in user_input.lower() for k in social_keywords) or len(user_input.split()) < 3:
            return {
                "answer": "Xin chào! Tôi là trợ lý pháp luật VN-Law. Tôi có thể giúp gì cho bạn?",
                "lst_Relevant_Documents": [] 
            }
        # -----------------------------

        # Nếu là câu hỏi bình thường -> Gọi Google Search
        answer, relevant_links = search_tools.Search_Docs_From_Tools(user_input)
        
        # Xử lý nếu answer bị dính JSON (Do DeepSeek trả về)
        # Nếu answer là chuỗi JSON {"answer": "..."} thì parse ra
        import json
        try:
            if answer.strip().startswith("{") and "answer" in answer:
                parsed = json.loads(answer)
                answer = parsed.get("answer", answer)
        except:
            pass

        return {
            "answer": answer,
            "lst_Relevant_Documents": relevant_links
        }
    except Exception as e:
        # Fallback an toàn thay vì sập server
        print(f"❌ Lỗi Search Web: {e}")
        return {
            "answer": "Xin lỗi, hiện tại tôi không thể tìm kiếm trên Internet.",
            "lst_Relevant_Documents": []
        }

# ==============================================================================
# 2. ENDPOINT CHÍNH (RAG + AUTO SEARCH)
# ==============================================================================
@router.post("/chatbot-with-deepseek")
def chatbot_with_gemini(query: ChatbotQuery):
    try:
        user_input = query.query
        print(f"🔹 [Chatbot] Nhận câu hỏi: {user_input}")

        # 1. Gọi RAG (DeepSeek + Qdrant)
        # Hàm này trả về 3 biến: Câu trả lời, Danh sách tài liệu, Cờ báo hiệu cần search web
        answer, lst_Article_Quote, need_web_search = rag.get_Article_Content_Results(user_input)
        
        # 2. KIỂM TRA: Nếu RAG yêu cầu tìm Web (Do không có dữ liệu nội bộ)
        if need_web_search:
            print(f"⚠️ Local RAG không có dữ liệu. Chuyển sang Google Search...")
            try:
                # Gọi lại logic Search Web ở trên
                web_result = chatbot_with_search_web(query)
                return {
                    "answer": web_result["answer"],
                    "lst_Relevant_Documents": web_result["lst_Relevant_Documents"],
                    "use_web_search": True
                }
            except Exception as e:
                print(f"❌ Google Search lỗi: {e}")
                return {
                    "answer": answer, # Trả về câu trả lời mặc định của RAG
                    "lst_Relevant_Documents": [],
                    "use_web_search": False
                }

        # 3. Chuẩn hóa danh sách tài liệu từ Qdrant (Nếu có)
        formatted_docs = []
        if lst_Article_Quote:
            for doc in lst_Article_Quote:
                if isinstance(doc, str):
                    formatted_docs.append(doc)
                elif isinstance(doc, dict) and "content" in doc:
                    formatted_docs.append(doc["content"])
                else:
                    formatted_docs.append(str(doc))
        
        return {
            "answer": answer,
            "lst_Relevant_Documents": formatted_docs,
            "use_web_search": False
        }

    except Exception as e:
        print(f"❌ Lỗi Chatbot System: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")