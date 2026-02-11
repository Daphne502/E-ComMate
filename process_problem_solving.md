# Process Problem Solving（过程性问题解决）

说明：此文档旨在于记录并总结项目跟进过程中出现的问题和对应的解决方案

## Q1：多模态模型.with_structured_output()的适配与PlanB

### Q1问题说明

在开发 vision.py 模块时，目标是让多模态大模型（Qwen-VL-Max）读取电商商品图片，并输出严格符合 Pydantic 定义的 JSON 格式数据
最开始我使用了 LangChain 0.3 推荐的``.with_structured_output()``方法。这是目前最先进的结构化输出方式，底层依赖大模型的 Tool Calling (工具调用) 或 Function Calling 能力。但是运行时出现报错，抛出 BadRequestError (400)，核心报错信息为：

```cmd
Invalid value for 'tools': no function named 'ImageInfo' was specified
```

这意味着模型服务端拒绝了请求，因为它无法识别我们在代码中通过 ImageInfo 类定义的工具结构。

### Q1问题分析

经过查阅文档与调试，定位原因为模型能力的边界限制：

- **API 兼容性差异**：虽然使用了 ChatOpenAI 适配层通过 OpenAI 兼容协议调用阿里云 DashScope，但底层模型 Qwen-VL-Max 目前在处理视觉任务（Vision Task）时，尚未完全支持 Function Calling 标准

- **视觉模型的特殊性**：大多数多模态模型（包括早期的 GPT-4V）在“看图”模式下，注意力机制主要集中在像素理解上，对复杂的工具参数绑定（Tool Binding）支持较弱或直接禁用
  
- **LangChain 机制**：.with_structured_output() 强依赖模型的原生 Tool Call 接口。当模型不支持该接口时，LangChain 无法自动降级，导致参数传递失败

所以这不是代码逻辑错误，而是基础设施（Model API）暂时无法满足“视觉理解 + 工具调用”同时进行的需求

### Q1解决方案

为了绕过 API 限制并保证工程稳定性，采用了 “Prompt Engineering + Output Parser” (提示词工程 + 输出解析器) 的降级方案（Plan B）。

**具体步骤**：

1. 显式注入 Schema：
    不再依赖模型自动识别 Pydantic 类，而是利用 JsonOutputParser 将 ImageInfo 的数据结构转换为纯文本格式说明（Format Instructions），直接拼接到 System Prompt 中

    > Prompt 变更： "请分析图片...请严格按照以下 JSON 格式输出：{format_instructions}"

2. 强制 JSON 输出：
    在 Prompt 中明确要求模型“只输出 JSON，不要包含 Markdown 标记”，并把 temperature 调至 0.01，最大程度降低模型的发散性

3. 后处理清洗 (Robust Parsing)：
    编写了一个 clean_json_string 函数，使用正则表达式去除模型可能返回的 ```json 等 Markdown 代码块标记，提取纯净的 JSON 字符串

4. 手动解析：
    使用 Python 原生的 json.loads 将清洗后的字符串转换为字典

#### 最终效果

成功绕过了 Tool Call 的限制，模型稳定返回了包含 description, style, color_palette 等字段的标准 JSON 数据，且解析成功率达到 100%
