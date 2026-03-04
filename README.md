# ⚖️ Vietnamese Legal Assistant using Agentic RAG

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103%2B-009688)
![React](https://img.shields.io/badge/React-18.0%2B-61DAFB)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-ff5252)
![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek_R1_Distill-blueviolet)

> **Đồ án Tốt nghiệp:** Ứng dụng kiến trúc Agentic RAG xây dựng hệ thống hỗ trợ tra cứu pháp luật Việt Nam.
> **Tác giả:** Vũ Việt Bách - Đại học Thủy Lợi (Phân hiệu TP.HCM)

## 📖 Giới thiệu (Introduction)
Hệ thống trợ lý ảo hỗ trợ tra cứu pháp luật Việt Nam được xây dựng nhằm giải quyết bài toán "ảo giác" (hallucination) thường gặp ở các Mô hình ngôn ngữ lớn (LLMs). Bằng cách kết hợp kiến trúc **Agentic RAG (Retrieval-Augmented Generation)** và các kỹ thuật Fine-tuning chuyên sâu, hệ thống đảm bảo đưa ra các câu trả lời chính xác, bám sát các bộ luật và văn bản pháp quy hiện hành của Việt Nam.

## ✨ Tính năng nổi bật (Key Features)
- **Truy xuất ngữ nghĩa chuẩn xác (Semantic Search):** Sử dụng mô hình Embedding chuyên biệt cho văn bản pháp luật Việt Nam (Fine-tuned với hàm mất mát MNRL và Matryoshka Loss).
- **Tái xếp hạng tài liệu (Reranking):** Tích hợp mô hình Cross-Encoder (Alibaba-NLP) để lọc và đưa các tài liệu liên quan nhất lên đầu.
- **Trích xuất thông tin (Machine Reading Comprehension - MRC):** Tích hợp mô hình BERT đã được fine-tune để trích xuất chính xác đoạn văn bản chứa câu trả lời.
- **Tạo sinh câu trả lời (Text Generation):** Sử dụng LLM DeepSeek-R1-Distill đã được tinh chỉnh (Fine-tuning qua kỹ thuật QLoRA) để hiểu tư duy logic pháp lý, định dạng GGUF chạy trên local (Ollama) đảm bảo bảo mật dữ liệu.
- **Hệ thống Agent linh hoạt:** Tích hợp Query Router và Query Rewriting để tự động phân tích và định tuyến câu hỏi của người dùng.

## 🏗️ Kiến trúc hệ thống (System Architecture)
Hệ thống được thiết kế theo kiến trúc Microservices, bao gồm các thành phần chính:
1. **Frontend:** ReactJS, Tailwind CSS (Giao diện người dùng tương tác).
2. **Backend:** Python, FastAPI, LangChain (Xử lý luồng hội thoại và Agentic RAG).
3. **Vector Database:** Qdrant (Lưu trữ và truy xuất vector embeddings).
4. **Local LLM Server:** Ollama (Triển khai mô hình DeepSeek đã fine-tune).


<img width="1780" height="762" alt="agentic1" src="https://github.com/user-attachments/assets/caceea39-a72a-4830-9926-844b75780c19" />


## 🛠️ Công nghệ sử dụng (Technologies)
- **AI & NLP:** LangChain, Hugging Face, LLaMA-Factory, Sentence Transformers.
- **Mô hình (Models):** DeepSeek, BERT, Alibaba-NLP Cross-Encoder.
- **Backend & Database:** FastAPI, Qdrant, MySQL.
- **Frontend:** ReactJS, Tailwind CSS.
- **Deployment:** Docker, Docker Compose.

## 🚀 Hướng dẫn cài đặt (Installation & Setup)

### 1. Yêu cầu hệ thống (Prerequisites)
- Python 3.9+
- Node.js & npm
- Docker & Docker Compose
- Ollama (để chạy LLM local)

### 2. Cài đặt Backend
```bash
# Clone repository
git clone [https://github.com/vuvietbach2/rag-chatbot.git](https://github.com/vuvietbach2/rag-chatbot.git)
cd rag-chatbot/backend

# Tạo môi trường ảo và kích hoạt
python -m venv venv
source venv/bin/activate  # Trên Windows dùng: venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Khởi chạy server FastAPI
uvicorn main:app --reload --port 8000
