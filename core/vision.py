import base64
import os
import json
import re
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
import config

class ImageInfo(BaseModel):
    """图片视觉分析结果"""
    description: str = Field(description="对图片中商品的详细外观描述，包括款式、图案等")
    style: str = Field(description="商品的风格，例如：复古、简约、运动、商务、街头等")
    color_palette: List[str] = Field(description="提取图片中的主色调，最多3个颜色")
    material: str = Field(description="推测商品的材质，例如：纯棉、皮革、丝绸、牛仔等")
    target_audience: str = Field(description="适合的消费人群，例如：职场新人、户外爱好者、学生等")

def clean_json_string(json_str):
    cleaned = re.sub(r'```json\s*', '', json_str)
    cleaned = re.sub(r'```', '', cleaned)
    return cleaned.strip()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path: str) -> dict:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片未找到: {image_path}")

    print(f"正在观察图片: {image_path} ...")
    
    parser = JsonOutputParser(pydantic_object=ImageInfo)
    
    llm = ChatOpenAI(
        model=config.VISION_MODEL_NAME,
        openai_api_key=config.API_KEY,
        openai_api_base=config.BASE_URL,
        temperature=0.01,
        max_tokens=1024
    )

    base64_image = encode_image(image_path)

    format_instructions = parser.get_format_instructions()
    
    prompt_text = f"""
    请作为一位资深的电商选品专家，仔细分析这张商品图片。
    请提取关键视觉属性，并严格按照 JSON 格式输出。
    
    {format_instructions}
    """

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            },
        ]
    )

    try:
        response = llm.invoke([message])
        content = response.content
        
        cleaned_content = clean_json_string(content)
        parsed_result = json.loads(cleaned_content)
        
        return parsed_result
        
    except Exception as e:
        print(f"视觉解析失败: {e}")
        if 'content' in locals():
            print(f"模型原始返回: {content}")
            
        return {
            "description": "图片解析失败",
            "style": "未知",
            "color_palette": [],
            "material": "未知",
            "target_audience": "未知"
        }