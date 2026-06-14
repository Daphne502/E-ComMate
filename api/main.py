import os
import time
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import GenerateResponse, HealthResponse
from core.workflow import create_workflow
from core.logging_config import setup_logging
setup_logging()

app = FastAPI(
    title="E-ComMate API",
    description="多模态电商营销文案生成 Agent",
    version="2.1.0",
)

# 允许 Streamlit 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """健康检查 — Docker / 负载均衡会调这个"""
    return HealthResponse(status="ok")

@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_copy(
    image: UploadFile = File(..., description="商品图片"),
    user_style: str = Form(..., description="文案风格，如：小红书种草"),
    words_limit: int = Form(100, description="字数上限"),
    user_note: str = Form("", description="用户补充要求"),
):
    """
    核心接口：上传图片 + 参数 → 返回文案与调试信息
    """
    # 1. 校验文件类型
    if image.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="仅支持 jpg/png 图片")

    # 2. 保存到临时文件（workflow 目前吃 image_path）
    suffix = os.path.splitext(image.filename or "upload.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await image.read()
        tmp.write(content)
        temp_path = tmp.name

    start = time.perf_counter()
    try:
        # 3. 调用 LangGraph（与原先 app.py 里 inputs 一致）
        workflow = create_workflow()
        inputs = {
            "image_path": temp_path,
            "user_style": user_style,
            "words_limit": str(words_limit),
            "user_note": user_note,
            "image_data": {},
            "retrieved_examples": [],
            "final_copy": "",
            "timings": {},
        }
        result = workflow.invoke(inputs)

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return GenerateResponse(
            final_copy=result.get("final_copy", ""),
            image_data=result.get("image_data", {}),
            retrieved_examples=result.get("retrieved_examples", []),
            elapsed_ms=elapsed_ms,
            timings=result.get("timings", {}),
        )
    finally:
        # 4. 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)