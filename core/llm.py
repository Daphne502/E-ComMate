from langchain_openai import ChatOpenAI
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
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

# Test
if __name__ == "__main__":
    try:
        print("正在连接阿里云 Qwen 模型...")
        model = get_llm()
        # 测试调用
        response = model.invoke("你好，请用一句话介绍你自己，并告诉我你的优势是什么？")
        print("\n 调用成功！模型回答如下：")
        print("-" * 30)
        print(response.content)
        print("-" * 30)
    except Exception as e:
        print(f"\n 出错了：{e}")