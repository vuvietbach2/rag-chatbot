import json
import re
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from source.core.config import Settings
from source.function.utils_shared import load_prompt_from_yaml 

class DeepSeek_Generate():
    def __init__(self, settings: Settings):
        self.settings = settings
        # --- CẤU HÌNH MODEL ---
        self.llm = ChatOllama(
            model="vn-law",
            base_url="http://localhost:11434",
            # [QUAN TRỌNG] Tăng nhiệt độ lên 0.6 để tránh bị kẹt vòng lặp suy nghĩ (Infinite Loop)
            temperature=0.6, 
            num_ctx=4096,
            keep_alive="1h"
        )
        
        # Load prompt router từ YAML (chỉ dùng cho router AI)
        self.prompt_router = load_prompt_from_yaml(settings, "classify_query")
        # Load prompt xã giao
        self.prompt_social = load_prompt_from_yaml(settings, "information_query")

    def clean_thinking(self, text: str) -> str:
        """Làm sạch chuỗi suy nghĩ và format thừa"""
        if not text: return ""
        # 1. Xóa thẻ <think>...</think>
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # 2. Xóa Markdown code block (```json ... ```)
        text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
        text = text.replace("```", "").strip()
        return text

    def format_docs(self, docs) -> str:
        """Chuẩn hóa tài liệu đầu vào"""
        if isinstance(docs, dict):
            return "\n\n".join([f"[{i+1}] {content}" for i, content in enumerate(docs.values())])
        if isinstance(docs, list):
            return "\n\n".join([f"[{i+1}] {content}" for i, content in enumerate(docs)])
        return str(docs)

    # ==========================================================================
    # 1. ROUTER HYBRID (ĐÃ FIX LỖI "HI" TRONG "KHI")
    # ==========================================================================
    def router_check(self, query: str) -> int:
        print(f"🧠 Router đang phân tích: {query}")
        query_lower = query.lower().strip()

        # --- BƯỚC 1: TỪ KHÓA LUẬT (BỔ SUNG THÊM TỪ VỰNG GIAO THÔNG/RƯỢU BIA) ---
        law_keywords = [
            # Nhóm từ khóa gốc
            "luật", "nghị định", "thông tư", "quyết định", "pháp luật", 
            "xử phạt", "bị phạt", "phạt bao nhiêu", "phạt tiền", 
            "tù", "án", "tố tụng", "khởi kiện", "tòa án",
            "ly hôn", "thừa kế", "đất đai", "bồi thường", "tranh chấp",
            "vi phạm", "giao thông", "hình sự", "dân sự", "lao động",
            "kết hôn", "tuổi", "doanh nghiệp", "thuế", "bảo hiểm", "bao nhiêu",
            
            # [MỚI] Nhóm từ khóa mở rộng (Fix lỗi "bị sao")
            "bị sao", "thế nào", "ra sao", "có được không", "cấm",
            "rượu", "bia", "cồn", "lái xe", "bằng lái", "đăng kiểm",
            "tạm giữ", "tước", "thu hồi"
        ]
        
        if any(k in query_lower for k in law_keywords):
            print(f"⚡ Router (Rule-based): Phát hiện từ khóa Luật -> Luồng 1")
            return 1

        # --- BƯỚC 2: TỪ KHÓA XÃ GIAO (ĐÃ XÓA 'HI' ĐỂ TRÁNH NHẦM LẪN) ---
        social_keywords = [
            "xin chào", "chào bạn", "hello", "bạn là ai", "tên gì", 
            "giúp gì", "hỗ trợ gì", "chức năng", "cảm ơn", "tạm biệt"
        ]
        
        # Kiểm tra từ khóa xã giao dài
        if any(k in query_lower for k in social_keywords):
            print(f"⚡ Router (Rule-based): Phát hiện câu chào hỏi -> Luồng 0")
            return 0
            
        # Kiểm tra từ "hi" một cách an toàn (chỉ bắt "hi" đứng một mình hoặc đầu câu)
        # Tránh bắt nhầm "khi", "nhiều", "thi"...
        if query_lower == "hi" or query_lower.startswith("hi "):
            print(f"⚡ Router (Rule-based): Phát hiện 'Hi' -> Luồng 0")
            return 0

        # --- BƯỚC 3: CHECK RÁC ---
        if len(query.split()) < 2 and query_lower not in ["hello", "chào"]:
             print(f"⚡ Router (Rule-based): Câu quá ngắn/vô nghĩa -> Luồng 2")
             return 2

        # --- BƯỚC 4: AI FALLBACK ---
        # Nếu không dính từ khóa nào ở trên, mới dùng AI
        try:
            chain = self.prompt_router | self.llm | StrOutputParser()
            result = chain.invoke({"query": query})
            clean_result = self.clean_thinking(result).strip()
            match = re.search(r'\b(0|1|2)\b', clean_result)
            if match:
                return int(match.group(1))
            return 1 # Fallback an toàn về Luật
        except Exception:
            return 1

    # ==========================================================================
    # 2. TRẢ LỜI LUẬT (ĐÃ TỐI ƯU HÓA TỐC ĐỘ)
    # ==========================================================================
    def generate_response(self, query: str, docs: dict) -> str:
        context_text = self.format_docs(docs)
        print(f"🤖 VN-LAW đang tra cứu luật: {query}")

        # Prompt trực tiếp - Ngắn gọn - Dễ hiểu cho AI
        template = """
        Bạn là Trợ lý Pháp luật Việt Nam.
        
        NHIỆM VỤ:
        Dựa vào các văn bản dưới đây, hãy trả lời câu hỏi ngắn gọn, chính xác.
        
        DỮ LIỆU:
        {context}
        
        CÂU HỎI: {original_query}
        
        YÊU CẦU ĐẦU RA:
        Chỉ trả về JSON theo định dạng sau (không giải thích thêm):
        {{
            "answer": "Nội dung câu trả lời..."
        }}
        """
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            # Gọi AI
            raw_response = chain.invoke({"original_query": query, "context": context_text})
            clean_response = self.clean_thinking(raw_response)
            
            # --- BỘ LỌC JSON THÔNG MINH ---
            # Cố gắng tìm chuỗi JSON {...} trong đống văn bản hỗn độn
            match = re.search(r'(\{.*\})', clean_response, re.DOTALL)
            if match:
                return match.group(1) # Trả về đúng phần JSON
            
            # Nếu AI không trả về JSON mà trả về text thường -> Tự đóng gói
            return json.dumps({
                "answer": clean_response,
                "lst_Article_Quote": [] 
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "answer": f"Xin lỗi, hệ thống đang bận. Lỗi: {str(e)}",
                "lst_Article_Quote": []
            }, ensure_ascii=False)

    # ==========================================================================
    # 3. TRẢ LỜI XÃ GIAO
    # ==========================================================================
    def generate_information(self, query: str, context: str) -> str:
        print(f"🤖 VN-LAW đang chat xã giao: {query}")
        chain = self.prompt_social | self.llm | StrOutputParser()
        try:
            raw_response = chain.invoke({"query": query, "context": context})
            return self.clean_thinking(raw_response)
        except Exception:
            return "Xin chào! Tôi là trợ lý ảo pháp luật VN-LAW. Tôi có thể giúp gì cho bạn?"