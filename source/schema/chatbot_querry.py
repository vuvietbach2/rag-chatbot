from pydantic import BaseModel

class ChatbotQuery(BaseModel):
    query: str