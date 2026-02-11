from langchain_openai import ChatOpenAI
import config

def get_llm():
    llm = ChatOpenAI(
        model=config.MODEL_NAME,      
        openai_api_key=config.API_KEY,  
        openai_api_base=config.BASE_URL,
        temperature=0.7,              
        max_tokens=500
    )
    return llm