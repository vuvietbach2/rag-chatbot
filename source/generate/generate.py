# --- patch_langchain.py (gọi ngay khi app khởi động) ---
from langchain_google_genai import ChatGoogleGenerativeAI # Import lại cho chắc
from langchain_core.output_parsers import StrOutputParser
from source.model.generate_model import Gemini
from source.function.utils_shared import load_prompt_from_yaml,clean_generated_queries
from source.core.config import Settings
from source.tool.google_search import GoogleSearchTool
class Gemini_Generate():
    def __init__(self,gemini_model:Gemini,settings:Settings):
          self.gemini_model=gemini_model
          self.yaml_path=settings
    def generate_query(self, original_query: str) -> list[str]:
        prompt = load_prompt_from_yaml(self.yaml_path,'query_generator')
        model = ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0
        )
        prompt = prompt.format_messages(original_query=original_query)
        query_generator_chain = (
           model | StrOutputParser()
        )
        result = query_generator_chain.invoke(prompt)
        generated_queries = result.strip().split('\n')
        generated_queries=clean_generated_queries(generated_queries)

        queries = [original_query] + generated_queries

        return queries    
    def generate_response(self,query: str,docs:dict) -> str:
        # docs = [doc for doc, _ in docs]
        # docs_dict = {i: doc for i, doc in enumerate(docs)}
        # docs_str = "\n".join(f"{k}: {v}" for k, v in docs_dict.items())
        docs = "\n".join(f"{k}: {v}" for k, v in docs.items())
        prompt_template=load_prompt_from_yaml(self.yaml_path,"response")
        response_model = ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0.2,
            max_tokens=10000,
            top_p=0.6,
        )
        prompt_template=prompt_template.format_messages(original_query=query,context=docs)
        response_chain =response_model | StrOutputParser()
        final_response = response_chain.invoke(prompt_template).strip()
        return final_response
    def classify_query(self, query: str) -> int:
        prompt=load_prompt_from_yaml(self.yaml_path,'classify_query')
        classify_model = ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0
        )
        prompt=prompt.format_messages(query=query)
        classify_chain = classify_model | StrOutputParser()
        classification = classify_chain.invoke(prompt).strip()
        return int(classification)
    def invalid_query(self,query:str)->str:
        prompt=load_prompt_from_yaml(self.yaml_path,'invalid_query')
        invalid_model=ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0
        )
        prompt=prompt.format_messages(query=query)
        invalid_chain = invalid_model | StrOutputParser()
        invalid = invalid_chain.invoke(prompt).strip()
        return invalid
    def generate_information(self,query:str,context)->str:
        prompt=load_prompt_from_yaml(self.yaml_path,'information_query')
        information_model=ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0
        )
        prompt=prompt.format_messages(query=query,context=context)
        information_chain=information_model | StrOutputParser()
        information=information_chain.invoke(prompt).strip()
        return information
    def extract_entities(self,query:str)->str:
        prompt=load_prompt_from_yaml(self.yaml_path,'query_extract_entities')
        extract_information_model=ChatGoogleGenerativeAI(
            google_api_key=self.gemini_model.key_manager.get_next_key(),
            model=self.gemini_model.model_gemini,
            temperature=0
        )
        prompt=prompt.format_messages(query=query)
        extract_chain=extract_information_model | StrOutputParser()
        extract_information=extract_chain.invoke(prompt).strip()
        return extract_information
        