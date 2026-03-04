import json
import re
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from source.core.config import Settings

# --- [BẮT ĐẦU MONKEY PATCH] ---
# Import module đang chứa hàm bị lỗi
import source.function.utils_shared as shared_utils

# Định nghĩa hàm parse mới xịn hơn, chấp nhận mọi thể loại lỗi
def better_parse_json(text_content):
    try:
        # 1. Thử parse trực tiếp
        return json.loads(text_content)
    except:
        try:
            # 2. Nếu lỗi, thử tìm nội dung trong ngoặc nhọn đầu-cuối
            # Kỹ thuật này bỏ qua hết rác ở đầu và đuôi (Extra data)
            match = re.search(r'(\{.*\})', text_content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                # 3. Nếu không tìm thấy JSON, coi toàn bộ text là câu trả lời
                return {"answer": text_content}
        except Exception as e:
            # 4. Cùng đường thì trả về text gốc luôn để không bao giờ crash
            return {"answer": text_content}

# GHI ĐÈ hàm cũ bằng hàm mới của chúng ta
print("🔧 Đã vá lỗi hàm parse_raw_json thành công!")
shared_utils.parse_raw_json = better_parse_json
# --- [KẾT THÚC MONKEY PATCH] ---

class Hybrid_Generate():
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # 1. DEEPSEEK (Local)
        self.local_llm = ChatOllama(
            model="deepseek-luat", 
            base_url="http://localhost:11434",
            temperature=0.1, 
            num_ctx=8192,
            keep_alive="1h"
        )

        # 2. GEMINI (Cloud)
        self.cloud_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key="AIzaSyC_GhDDP3nh19hs2BuXlpa3VjPp8WA0kYI", # <--- DÁN KEY VÀO ĐÂY
            temperature=0.3
        )

    def clean_thinking(self, text: str) -> str:
        if not text: return ""
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    def format_docs(self, docs) -> str:
        formatted_text = ""
        if isinstance(docs, dict):
            for i, (doc_id, content) in enumerate(docs.items(), 1):
                formatted_text += f"--- [Tài liệu {i}] ---\n{content}\n\n"
        elif isinstance(docs, list):
            for i, content in enumerate(docs, 1):
                formatted_text += f"--- [Tài liệu {i}] ---\n{content}\n\n"
        else:
            formatted_text = str(docs)
        return formatted_text

    def generate_response(self, query: str, docs: dict) -> str:
        context_text = self.format_docs(docs)

        # DEEPSEEK
        print(f"🤖 [Hybrid] DeepSeek đang phân tích: {query}...")
        analyze_prompt = PromptTemplate.from_template("""
        Nhiệm vụ: Trích xuất ý chính từ tài liệu để trả lời: "{question}"
        Tài liệu: {context}
        Yêu cầu: Ngắn gọn.
        """)
        
        try:
            chain_analyze = analyze_prompt | self.local_llm | StrOutputParser()
            analysis_result = chain_analyze.invoke({"question": query, "context": context_text})
            cleaned_analysis = self.clean_thinking(analysis_result)
        except:
            cleaned_analysis = context_text

        # GEMINI
        print("✨ [Hybrid] Gemini đang viết...")
        final_prompt = PromptTemplate.from_template("""
        Bạn là Luật sư. Dựa vào thông tin sau, hãy viết câu trả lời.
        Thông tin: {analysis}
        Câu hỏi: {question}
        Yêu cầu: Trả lời chi tiết, có mục "**Căn cứ pháp lý:**" ở cuối.
        """)

        try:
            chain_final = final_prompt | self.cloud_llm | StrOutputParser()
            final_response = chain_final.invoke({
                "question": query, 
                "analysis": cleaned_analysis
            })
            
            # Trả về JSON chuẩn
            return json.dumps({"answer": final_response.strip()}, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"answer": f"Lỗi: {str(e)}"}, ensure_ascii=False)