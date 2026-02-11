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
    words_limit: str  # 新增修改: 接收用户要求生成文案长度的量       
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
    limit = state.get('words_limit', '适中')  # 新增有关文案长度的量
    
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
    1. 文案整体调性要贴合{style}，像同领域博主的真实分享，避免模板化套话和生硬的分条列点，用流畅的段落自然串联内容。
    2. 用具体的使用体验和场景化描述来体现商品亮点，比如“这个奶白色在阳光下会有细闪，摸起来是那种糯糯的麂皮感”，而不是只说“颜色好看、材质高级”，同时避免一句话一段的碎片化表达。
    3. 可以用少量Emoji点缀，让语气更轻松，但别让表情盖过内容本身，也不要用“YYDS”“绝绝子”这类泛滥词。
    4. 段落长度适中，每段不超过3行，重点内容可适当加粗，保持阅读呼吸感，同时避免过度碎碎念，让信息传递更清晰。
    5. 用第一人称或朋友聊天的语气，比如“我自己用下来觉得…”，可以提一点无伤大雅的小缺点，显得更真实可信，同时融入个人故事或场景，增强代入感。
    6. 避免绝对化表达，用主观偏好代替客观吹捧，比如“我更推荐搭配白内搭，会更清爽”，同时可以加入精准的个人数据或体验细节，如“我158/46kg，裙子腰头松紧刚好”，提升可信度。
    7. 结尾用1-2句真心总结，搭配精准的话题标签，可加一句简短的后续反馈预告，让文案更完整且有延续性。
    8. 根据图片信息的内容量来控制文案长度,如果商品图较为简单,就无需凑字数
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