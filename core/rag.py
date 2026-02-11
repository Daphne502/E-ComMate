import os
import pandas as pd
import config
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

def get_embeddings():
    """
    使用阿里云的 Embedding 服务
    """
    return OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL_NAME,
        openai_api_key=config.API_KEY,
        openai_api_base=config.BASE_URL,
        check_embedding_ctx_length=False 
    )

def initialize_rag():
    """
    如果本地已经有数据库，直接加载；
    如果没有，从 CSV 初始化。
    """
    db_path = config.VECTOR_DB_DIR
    embeddings = get_embeddings()

    if os.path.exists(db_path) and os.listdir(db_path):
        print("检测到本地向量库，正在加载...")
        vector_store = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
    else:
        print("正在初始化向量库 (第一次运行会比较慢)...")
        csv_path = os.path.join("data", "styles.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"找不到数据文件: {csv_path}")
            
        df = pd.read_csv(csv_path)
        
        documents = []
        for _, row in df.iterrows():
            doc = Document(
                page_content=row['content'],
                metadata={"style": row['style']}
            )
            documents.append(doc)
            
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=db_path
        )
        print("向量库构建完成！")
        
    return vector_store

def retrieve_examples(query_style: str, k: int = 3):
    """
    根据用户想要的风格 (query_style)，检索 k 个最相似的文案范例。
    """
    vector_store = initialize_rag()
    
    print(f"正在检索风格: {query_style} ...")
    
    results = vector_store.similarity_search(query_style, k=k)
    
    examples = [doc.page_content for doc in results]
    return examples