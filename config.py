import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus") # 默认使用 qwen-plus
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen-vl-max")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v1")

VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

if not API_KEY:
    raise ValueError("未检测到 API Key，请检查 .env 文件！")