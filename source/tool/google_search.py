import requests
from typing import List
from source.core.config import Settings
from bs4 import BeautifulSoup
import urllib3

# Tắt cảnh báo SSL không an toàn
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GoogleSearchTool:
    def __init__(self, setting: Settings):
        self.api_key = setting.GOOGLE_SEARCH_API
        self.cse_id = setting.TOOL_SEARCH_API # Lưu ý: Kiểm tra lại tên biến trong .env là TOOL_SEARCH hay TOOL_SEARCH_API

    def search(self, query: str, num_results: int = 5) -> List[str]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cse_id,
            "num": num_results
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ Google API Error: {response.text}")
                return []
            
            results = response.json()
            links = []
            
            # Dùng .get để an toàn hơn, tránh KeyError
            items = results.get("items", [])
            if not items:
                print("⚠️ Google Search không trả về kết quả nào.")
                
            for item in items:
                link = item.get("link")
                if link:
                    links.append(link)
            return links
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google API: {str(e)}")
            return []

    def extract_text_from_url(self, url: str) -> str:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            )
        }

        try:
            # verify=False để bỏ qua lỗi SSL của một số trang web chính phủ/cũ
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                verify=False 
            )
            
            if response.status_code != 200:
                return f"" # Trả về rỗng nếu lỗi, để không làm nhiễu AI

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Xóa script và style
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Cắt ngắn bớt nếu quá dài để tránh tràn context của AI
            return text[:4000] 

        except Exception as e:
            print(f"⚠️ Không thể đọc nội dung từ {url}: {str(e)}")
            return ""

    def extract_texts_from_links(self, links: List[str]) -> List[str]:
        texts = []
        for url in links:
            text = self.extract_text_from_url(url)
            if text and len(text) > 100: # Chỉ lấy bài viết có nội dung đủ dài
                texts.append(f"Nguồn: {url}\nNội dung: {text}")
        return texts