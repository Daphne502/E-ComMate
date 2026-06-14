from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import START
from langgraph.graph import StateGraph, END

from core.llm import get_llm
from core.vision import analyze_image
from core.rag import retrieve_examples

import time
from core.logging_config import get_logger
logger = get_logger("workflow")

def merge_timings(old: Dict[str, int], new: Dict[str, int]) -> Dict[str, int]:
    """LangGraph reducer：合并各节点的 timings，而不是覆盖"""
    if old is None:
        old = {}
    if new is None:
        new = {}
    return {**old, **new}

# 定义State
class AgentState(TypedDict):
    # 用户输入
    image_path: str        
    user_style: str
    words_limit: str  # FourthCommit新增修改: 接收用户要求生成文案长度的量       
    user_note: str  # refactor: 接收用户特定需求
    # 中间量处理
    image_data: Dict      
    retrieved_examples: List[str] 
    # 模型输出
    final_copy: str
    # 新增：各节点耗时（毫秒）
    timings: Annotated[Dict[str, int], merge_timings]

# 定义Nodes
def vision_node(state: AgentState) -> Dict:
    t0 = time.perf_counter()
    logger.info("[Vision Node] 开始解析: %s", state['image_path'])
    
    try:
        attributes = analyze_image(state['image_path'])
    except Exception as e:
        logger.exception("视觉模块报错，使用默认值")
        attributes = {
            "description": "未知商品",
            "style": "未知",
            "color_palette": [],
            "material": "未知",
            "target_audience": "未知",
        }
    elapsed = int((time.perf_counter() - t0) * 1000)
    logger.info("[Vision Node] 完成，耗时 %dms", elapsed)

    return {
        "image_data": attributes,
        "timings": {"vision_ms": elapsed},
    }

def retrieve_node(state: AgentState) -> Dict:
    t1 = time.perf_counter()
    logger.info("[Retrieval Node] 开始检索: %s", state['user_style'])

    try:
        examples = retrieve_examples(state['user_style'], k=3)
    except Exception as e:
        logger.exception("RAG 模块报错，使用默认空值")
        examples = ["暂无参考范例"]
        
    elapsed = int((time.perf_counter() - t1) * 1000)
    logger.info("[Retrieval Node] 完成，耗时 %dms", elapsed)

    return {
        "retrieved_examples": examples,
        "timings": {"retrieve_ms": elapsed},
    }

def generate_node(state: AgentState) -> Dict:
    t2 = time.perf_counter()
    logger.info("[Generation Node] 开始生成: %s", state['image_path'])

    attrs = state['image_data']
    examples = "\n".join([f"- {ex}" for ex in state['retrieved_examples']])
    style = state['user_style']
    limit = state.get('words_limit', '适中')  # FourthCommit新增有关文案长度的量
    note = state.get('user_note', '无') # refactor: 获取用户备注
    
    # refactor: 增强Prompt
    prompt = f"""
    你是一个金牌电商文案撰写专家。请根据以下信息撰写一篇吸引人的营销文案。

    【商品视觉信息】：
    {attrs}

    【用户指定风格】：
    {style}

    【长度要求】： 
    {limit}
    
    【用户特别要求】：{note}  <-- 必须优先满足这一点
    【字数限制】：控制在 {limit} 字左右（+/- 30字）

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
    
    elapsed = int((time.perf_counter() - t2) * 1000)
    logger.info("[Generation Node] 完成，耗时 %dms", elapsed)

    return {
        "final_copy": response.content,
        "timings": {"generate_ms": elapsed}
    }

def create_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("vision_step", vision_node)
    workflow.add_node("retrieve_step", retrieve_node)
    workflow.add_node("generate_step", generate_node)

    # 并行：START 同时触发 vision 和 retrieve
    workflow.add_edge(START, "vision_step")
    workflow.add_edge(START, "retrieve_step")

    # generate 等两个节点都完成
    workflow.add_edge("vision_step", "generate_step")
    workflow.add_edge("retrieve_step", "generate_step")
    workflow.add_edge("generate_step", END)

    return workflow.compile()