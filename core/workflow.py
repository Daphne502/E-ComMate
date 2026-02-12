from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

from core.llm import get_llm
from core.vision import analyze_image
from core.rag import retrieve_examples

# 定义State
class AgentState(TypedDict):
    # 用户输入
    image_path: str        
    user_style: str
    words_limit: str  # FourthCommit新增修改: 接收用户要求生成文案长度的量       
    # 中间量处理
    image_data: Dict      
    retrieved_examples: List[str] 
    # 模型输出
    final_copy: str 

# 定义Nodes
def vision_node(state: AgentState) -> Dict:
    """
    节点：视觉解析
    输入：image_path
    输出：更新 image_data
    """
    print(f"\n [Vision Node] 正在解析图片: {state['image_path']} ...")
    
    try:
        attributes = analyze_image(state['image_path'])
    except Exception as e:
        print(f"视觉模块报错: {e}，使用默认空值")
        attributes = {"description": "未知商品", "style": "未知", "color": "未知"}
    
    # 返回的内容会合并到 State 中
    return {"image_data": attributes}

def retrieve_node(state: AgentState) -> Dict:
    """
    节点：RAG 检索
    输入：user_style
    输出：更新 retrieved_examples
    """
    style = state['user_style']
    print(f"\n [Retrieval Node] 正在检索风格: {style} ...")
    
    try:
        examples = retrieve_examples(style, k=3)
    except Exception as e:
        print(f"RAG 模块报错: {e}，使用默认空值")
        examples = ["暂无参考范例"]
        
    return {"retrieved_examples": examples}

def generate_node(state: AgentState) -> Dict:
    """
    节点：文案生成
    输入：image_data, retrieved_examples, user_style, words_limit
    输出：更新 final_copy
    """
    print("\n [Generation Node] 正在生成最终文案 ...")
    
    # 1. 获取所有上下文
    attrs = state['image_data']
    examples = "\n".join([f"- {ex}" for ex in state['retrieved_examples']])
    style = state['user_style']
    limit = state.get('words_limit', '适中')  # FourthCommit新增有关文案长度的量
    
    # 2. 构建 Prompt
    prompt = f"""
    你是一个金牌电商文案撰写专家。请根据以下信息撰写一篇吸引人的营销文案。

    【商品视觉信息】：
    {attrs}

    【用户指定风格】：
    {style}

    【长度要求】： 
    {limit}
    
    【参考高分范例】（请学习其语气、结构，但不要照抄）：
    {examples}
    
    【要求】：
    1. 必须符合指定的“{style}”风格。
    2. 突出商品的视觉亮点（如颜色、材质）。
    3. 不要用“YYDS”“绝绝子”这类泛滥词。
    4. 输出格式清晰，不要包含“根据以上信息...”等废话，直接输出文案内容
    """

    # 3. 调用 LLM
    llm = get_llm()
    response = llm.invoke(prompt)  
    
    return {"final_copy": response.content}

# Graph Construction
def create_workflow():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("vision_step", vision_node)
    workflow.add_node("retrieve_step", retrieve_node)
    workflow.add_node("generate_step", generate_node)
    
    # 流程：Start -> Vision -> Retrieve -> Generate -> End
    workflow.set_entry_point("vision_step")
    workflow.add_edge("vision_step", "retrieve_step")
    workflow.add_edge("retrieve_step", "generate_step")
    workflow.add_edge("generate_step", END)
    
    app = workflow.compile()
    return app