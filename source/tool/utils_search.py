import json 
import traceback
from source.function.utils_shared import clean_code_fence_safe, parse_raw_json
from source.extract.utils_extract import Extract_Information
from source.core.config import Settings
from source.generate.generate import Gemini_Generate # Hoặc DeepSeek_Generate tùy import thực tế của bạn
from source.tool.google_search import GoogleSearchTool

class Utils_Search_Tools:
    def __init__(self, setting: Settings, gemini_func: Gemini_Generate, extract_func: Extract_Information, google_search_tools: GoogleSearchTool):
        self.setting = setting
        self.gemini_func = gemini_func
        self.extract_func = extract_func
        self.google_search_tools = google_search_tools
    
    def Search_Docs_From_Tools(self, query):
        # Khởi tạo trước để tránh lỗi nếu try thất bại ngay dòng đầu
        lst_links = []
        
        try:
            print(f"🌍 Đang tìm kiếm Google cho: {query}")
            
            # 1. Tìm kiếm Link
            lst_links = self.google_search_tools.search(query)
            if not lst_links:
                return "Xin lỗi, tôi không tìm thấy thông tin nào trên Internet.", []

            # 2. Đọc nội dung từ Link
            lst_docs = self.google_search_tools.extract_texts_from_links(lst_links)
            
            # 3. Rút gọn nội dung (Nếu có model Extract)
            # Kiểm tra xem lst_docs có rỗng không trước khi predict
            if lst_docs:
                lst_reduce_docs = self.extract_func.predict(lst_docs, query)
            else:
                lst_reduce_docs = []

            # 4. Gọi AI trả lời
            result_final = self.gemini_func.generate_response(query, lst_reduce_docs)
            
            # 5. Xử lý kết quả JSON
            answer_result = clean_code_fence_safe(result_final)
            answer_result_json = parse_raw_json(answer_result)
            
            final_answer = answer_result_json.get('answer', str(answer_result_json))
            
            # 6. Chọn lọc Link tham khảo
            # Nếu AI trả về 'key' (index các bài viết đã dùng) thì lấy theo AI
            # Nếu không (do prompt đơn giản), mặc định lấy 3 link đầu tiên
            ai_selected_keys = answer_result_json.get('key', [])
            relevant_links = []
            
            if ai_selected_keys and isinstance(ai_selected_keys, list):
                for k in ai_selected_keys:
                    if isinstance(k, int) and 0 <= k < len(lst_links):
                        relevant_links.append(lst_links[k])
            
            # Fallback: Nếu không có key nào, lấy top 3 link tìm được
            if not relevant_links:
                 relevant_links = lst_links[:3]

            return final_answer, relevant_links

        except Exception as e:
            print(f"❌ Lỗi Search Tools: {str(e)}") # Đã sửa lỗi concatenate str
            traceback.print_exc() # In chi tiết lỗi để debug
            
            error_message = "Xin lỗi, hệ thống gặp sự cố khi tổng hợp thông tin từ Internet."
            return error_message, lst_links