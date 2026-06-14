from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GenerateResponse(BaseModel):
    """生成文案的响应体"""
    final_copy: str = Field(..., description="最终营销文案")
    image_data: Dict[str, Any] = Field(default_factory=dict, description="视觉解析结果")
    retrieved_examples: List[str] = Field(default_factory=list, description="RAG 检索到的范例")
    elapsed_ms: Optional[int] = Field(None, description="总耗时(毫秒)")
    timings: Optional[Dict[str, int]] = Field(   # ← 新增
        default_factory=dict,
        description="各节点耗时(ms)，如 vision_ms / retrieve_ms / generate_ms",
    )
class HealthResponse(BaseModel):
    status: str = "ok"