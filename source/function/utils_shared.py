import yaml
from langchain_core.prompts import ChatPromptTemplate
from source.core.config import Settings
import textwrap
import os
import json
import re
from sentence_transformers import util
from source.model.embedding_model import Sentences_Transformer_Embedding

def load_prompt_from_yaml(settings: Settings, section: str) -> ChatPromptTemplate:
    current_dir = os.path.dirname(__file__)
    yaml_path = os.path.join(current_dir, '..', 'core', settings.YAML_PATH)
    yaml_path = os.path.abspath(yaml_path)
    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    messages = yaml_data['prompts'][section]['messages']
    return ChatPromptTemplate.from_messages(
        [(msg['role'], msg['content']) for msg in messages]
    )

def load_information_from_json(settings:Settings,model_embedding:Sentences_Transformer_Embedding):
    current_dir=os.path.dirname(__file__)
    json_path=os.path.join(current_dir,'..','core',settings.PATH_INFOR)
    json_path=os.path.abspath(json_path)
    with open(json_path,'r',encoding='utf-8') as f:
        data=json.load(f)
    corpus=[item['content'] for item in data]
    corpus_embedding=model_embedding.embeddings_bkai.embed_documents(corpus)
    return corpus,corpus_embedding

def search_from_json(corpus_embedding,corpus,query,model_embedding:Sentences_Transformer_Embedding):
    query_embedding=model_embedding.embeddings_bkai.embed_query(query)
    cos_scores = util.cos_sim(query_embedding, corpus_embedding)[0]
    top_results = cos_scores.argsort(descending=True)[:5]
    results=[]
    for idx in top_results:
        results.append(corpus[idx])
    return "\n".join(results)

def clean_generated_queries(queries):
    cleaned_queries = []
    for query in queries:
        if '```' in query:
            continue
        if len(query.split()) < 5:
            continue
        cleaned_queries.append(query)
    return cleaned_queries

def extract_json_dict(text):
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        return json.loads(json_str)
    else:
        raise ValueError("Không tìm thấy nội dung JSON hợp lệ.")
    
def clean_code_fence_safe(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        if lines[0].strip() == "```" or lines[0].strip().startswith("```"):
            lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()

# ====================================================================
# [ĐÃ SỬA] Hàm parse_raw_json mới - Chấp nhận mọi dữ liệu
# ====================================================================
def parse_raw_json(raw_text: str) -> dict:
    """
    Hàm đọc JSON an toàn. Không dùng Regex hẹp hòi nữa.
    Ưu tiên 1: Đọc thẳng JSON.
    Ưu tiên 2: Tìm JSON trong ngoặc {}.
    """
    text = raw_text.strip()
    parsed_data = {}

    # Cách 1: Parse trực tiếp (Nhanh và chuẩn nhất)
    try:
        parsed_data = json.loads(text)
    except:
        # Cách 2: Nếu lỗi, thử tìm nội dung trong ngoặc nhọn đầu tiên và cuối cùng
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                clean_json = match.group(1)
                parsed_data = json.loads(clean_json)
        except:
            pass
            
    # --- QUAN TRỌNG: MAPPING DỮ LIỆU ---
    # Đảm bảo đầu ra luôn có key 'lst_Article_Quote' để Web hiện nút xanh
    
    # 1. Lấy câu trả lời
    answer = parsed_data.get("answer", "")
    if not answer and not parsed_data: # Nếu thất bại hoàn toàn
        answer = raw_text

    # 2. Lấy danh sách tài liệu
    # DeepSeek có thể trả về các tên key khác nhau, ta tóm hết lại
    documents = parsed_data.get("lst_Article_Quote", []) or \
                parsed_data.get("relevant_docs", []) or \
                parsed_data.get("documents", []) or \
                parsed_data.get("context", [])

    return {
        "answer": str(answer),
        "lst_Article_Quote": documents # <-- Đây là biến quyết định hiển thị
    }