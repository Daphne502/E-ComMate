# E-ComMate：多模态电商营销文案自动化生成 Agent

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/daphne502/E-ComMate) ![Python](https://img.shields.io/badge/Python-3.12-blue.svg) ![LangGraph](https://img.shields.io/badge/LangGraph-1.0-green.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.128-teal.svg) ![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B.svg) ![Redis](https://img.shields.io/badge/Redis-Upstash%20%2F%20Local-red.svg)

上传商品图片，自动理解外观与卖点，结合风格范例生成多平台营销文案。支持小红书、京东/淘宝电商、朋友圈、抖音直播等文风，可设置字数与补充要求。

---

## 分支说明

| 分支 | 用途 | 部署方式 |
|:---|:---|:---|
| [`main`](https://github.com/Daphne502/E-ComMate/tree/main) | 本地开发、Docker Compose、评测 | 双终端 / `docker compose up` |
| [`hf-clean`](https://github.com/Daphne502/E-ComMate/tree/hf-clean) | **Hugging Face Spaces 线上 Demo** | 单容器 supervisord + Upstash Redis |

> 在线 Demo 运行在 **`hf-clean`** 分支。克隆仓库后请先确认分支：  
> `git checkout main`（本地） / `git checkout hf-clean`（复现 HF 部署）

---

## 在线体验

### [Hugging Face Spaces 在线 Demo](https://daphne502-e-commate.hf.space)

**示例商品图（`assets/`）：**

|      服饰       |      潮玩       |      食品       |
| :-------------: | :-------------: | :-------------: |
| <img src="assets/demo_image1.jpg" width="200" height="267" alt="Demo Screenshot"> | <img src="assets/demo_image2.jpg" width="200" height="200" alt="Demo Screenshot"> | <img src="assets/demo_image3.jpg" width="200" height="220" alt="Demo Screenshot"> |

---

## 核心痛点与解决方案

| 核心痛点          | E-ComMate 解决方案                                     | 技术支撑                             |
| :---------------- | :----------------------------------------------------- | :----------------------------------- |
| **视觉理解缺失**  | 从商品图提取颜色、材质、版型等结构化属性，减少「瞎编」 | **Qwen-VL-Max** 多模态大模型         |
| **风格同质化**    | 按平台切换文风，检索相似高分范例再生成                 | **RAG** + **ChromaDB** metadata 过滤 |
| **流程不可控**    | 视觉解析、风格检索、文案生成解耦，节点可观测           | **LangGraph** StateGraph             |
| **Demo 难工程化** | UI / API / Agent 三层分离，支持容器化与缓存            | **FastAPI** + **Docker** + **Redis** |

---

## 系统架构

### 逻辑架构（前后端分离）

```mermaid
flowchart TB
    START(("START")) --> Vision["vision_step<br/>视觉解析"]
    START --> Retrieve["retrieve_step<br/>风格 RAG"]
    Vision --> Generate["generate_step<br/>文案生成"]
    Retrieve --> Generate
    Generate --> END(("END"))
```

设计要点：

- Vision 与 Retrieve 无数据依赖，从 `START` 扇出并行，缩短总耗时
- Retrieve 先查 Redis，未命中再查 ChromaDB，结果按风格缓存（TTL 1h）
- API 返回 `timings`（各节点毫秒耗时），便于性能分析与面试演示

---

## 技术栈

| 层级       | 技术                                                         |
| :--------- | :----------------------------------------------------------- |
| 大模型     | 通义千问 Qwen-VL-Max（视觉）、Qwen-Plus（生成）、text-embedding-v1（向量）|
| Agent 编排 | LangChain / LangGraph（StateGraph + 并行边 + timings reducer） |
| RAG        | ChromaDB 本地向量库 + metadata 风格过滤                      |
| 缓存       | Redis（本地 Docker / 线上 Upstash Serverless）               |
| 后端       | FastAPI + Uvicorn                                            |
| 前端       | Streamlit                                                    |
| 部署       | `main`：Docker Compose 三服务；`hf-clean`：HF Spaces 单容器 supervisord + Upstash Redis |
| 评测       | 自研规则评测脚本（12 条用例，三品类 × 四风格）               |

---

## 工程亮点

| 优化项        | 做法                                                         | 效果                                                 |
| :------------ | :----------------------------------------------------------- | :--------------------------------------------------- |
| API 网关层    | Streamlit 通过 `/api/v1/generate` 调用，不再直接 invoke Agent | 对齐生产架构，OpenAPI 可联调                         |
| RAG 单例      | 向量库模块级懒加载，避免每次请求 reload                      | 消除重复初始化开销                                   |
| metadata 过滤 | `filter={"style": mapped_style}` 先筛风格再语义检索          | 减少跨风格污染                                       |
| Redis 缓存    | key: `ecommate:v1:style:{style}:k3`                          | 同风格 `retrieve_ms` 1949ms → 2ms                    |
| 并行编排      | Vision ∥ Retrieve → Generate                                 | 总耗时 ≈ max(Vision, Retrieve) + Generate            |
| 可观测性      | 结构化 logging + API 返回 `node_timings`                     | 各节点耗时透明                                       |
| 质量回归      | `eval/run_eval.py` 批量评测                                  | 12 条规则用例通过率 100%（回归测试，非人工美学评分） |

> 评测说明：当前为规则型回归测试（非空、Vision 有效、长度、备注关键词），用于 Prompt/流程改动后的快速验证，不代表主观文案质量上限。

---

## 目录结构

**共用（两分支一致）：** `api/`、`core/`、`eval/`、`assets/`、`data/`、`app.py`、`config.py`、`requirements.txt`

**`main` 分支额外文件：**

```txt
E-ComMate/
├── docker-compose.yml        # 本地三服务：api + streamlit + redis
├── Dockerfile                # 本地 API 镜像（docker-compose 使用）
├── Dockerfile.streamlit      # 本地 Streamlit 镜像
└── .env.example
```

**`hf-clean` 分支额外文件（HF Spaces 部署）：**

```txt
E-ComMate/
├── Dockerfile                # HF 单容器镜像（supervisord 管理双进程）
├── supervisord.conf          # API(8000) + Streamlit(7860)
├── docker-entrypoint.sh      # 启动时检查/构建 ChromaDB
├── Dockerfile.api            # 保留，供参考
├── Dockerfile.streamlit      # 保留，供参考
└── docker-compose.yml        # 保留，本地调试可用
```

---

## 快速开始

### 1. 克隆与环境变量

```bash
git clone https://github.com/Daphne502/E-ComMate.git
cd E-ComMate
git checkout main   # 本地开发（默认）
# git checkout hf-clean   # 仅当需要复现 HF 部署时
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # 填入 DASHSCOPE_API_KEY
```

`.env` 必填项：

```bash
DASHSCOPE_API_KEY=your_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
VISION_MODEL_NAME=qwen-vl-max
EMBEDDING_MODEL_NAME=text-embedding-v1
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_TTL=3600
ECOMMATE_API_URL=http://127.0.0.1:8000
```

### 2. 本地开发（`main` 分支 · 双终端）

**终端 1 — API：**

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 — Streamlit：**

```bash
streamlit run app.py
```

| 入口     | 地址                                            |
| :------- | :---------------------------------------------- |
| 前端     | [http://127.0.0.1:8501](http://127.0.0.1:8501/) |
| API 文档 | <http://127.0.0.1:8000/docs>                      |
| 健康检查 | <http://127.0.0.1:8000/health>                    |

### 3. 本地 Docker Compose（`main` 分支 · 推荐演示）

```docker
docker compose up --build
```

| 服务      | 地址                                            |
| :-------- | :---------------------------------------------- |
| Streamlit | [http://127.0.0.1:8501](http://127.0.0.1:8501/) |
| FastAPI   | <http://127.0.0.1:8000/docs>                    |
| Redis     | localhost:6379                                  |

`data/` 目录挂载持久化，ChromaDB 不会每次重建。

### 4. Hugging Face Spaces 部署（单容器方案）

> ⚠️ **请使用 [`hf-clean`](https://github.com/Daphne502/E-ComMate/tree/hf-clean) 分支。**  
> HF Space 在 Settings → Repository 中指定分支为 `hf-clean`。  
> `main` 分支不含 supervisord 单容器配置，无法直接用于 HF Docker Space。

HF Spaces 仅暴露一个端口，采用**单 Docker 容器 + supervisord** 同时运行 API 与 Streamlit：

| 进程 | 命令                                                         | 端口        |
| :--- | :----------------------------------------------------------- | :---------- |
| API  | `uvicorn api.main:app --host 127.0.0.1 --port 8000`          | 容器内 8000 |
| UI   | `streamlit run app.py --server.port 7860 --server.address 0.0.0.0` | 对外 7860 |

容器内 Streamlit 通过 `ECOMMATE_API_URL=http://127.0.0.1:8000` 访问 API。
**Redis（Upstash）**： 在 HF Space → Settings → Secrets 中配置：

```bash
REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
CACHE_TTL=3600
DASHSCOPE_API_KEY=sk-xxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

> HF 环境无本地 Redis，需使用 [Upstash Redis](https://upstash.com/) 等 Serverless Redis，  
> `REDIS_URL` 格式为 `rediss://...`（注意双 s 表示 TLS）。未配置时自动降级为 ChromaDB 直连。

未配置 `REDIS_URL` 时自动降级为直连 ChromaDB，功能正常，检索稍慢。
**ChromaDB:** 首次启动时 `docker-entrypoint.sh` 会从 `styles.csv` 自动构建向量库（约 1–2 分钟）。

---

## API 说明

### `GET /health`

健康检查，用于 Docker / 负载均衡探活。

**响应：**

```json
{"status": "ok"}
```

### `POST /api/v1/generate`

上传商品图并生成文案。

**请求（multipart/form-data）：**

| 字段          | 类型   | 说明                                               |
| :------------ | :----- | :------------------------------------------------- |
| `image`       | file   | 商品图片（jpg/png）                                |
| `user_style`  | string | 小红书种草 / 京东/淘宝电商 / 朋友圈私域 / 抖音直播 |
| `words_limit` | int    | 字数上限，默认 100                                 |
| `user_note`   | string | 补充要求，如「突出618」                            |

**响应示例：**

```json
{
  "final_copy": "...",
  "image_data": {
    "description": "...",
    "style": "简约",
    "color_palette": ["浅粉色", "深棕色"],
    "material": "针织棉",
    "target_audience": "都市年轻女性"
  },
  "retrieved_examples": ["...", "...", "..."],
  "elapsed_ms": 6034,
  "timings": {
    "vision_ms": 4622,
    "retrieve_ms": 2,
    "generate_ms": 1403
  }
}
```

---

## 批量评测

```python
python eval/run_eval.py
```

测试集覆盖 **服饰 / 潮玩 / 食品** 三类商品、**四种平台风格**，共 12 条用例。
报告输出至 `eval/eval_report.json`。

**最近一次评测摘要：**

| 指标             | 数值         |
| :--------------- | :----------- |
| 通过率           | 100% (12/12) |
| 平均总耗时       | 7658 ms      |
| 平均 retrieve_ms | 194 ms       |

---

## 开发日志

| 版本 | 内容                                                         |
| :--- | :----------------------------------------------------------- |
| v1.0 | MVP：Qwen-Plus 文案生成                                      |
| v1.1 | Qwen-VL 视觉解析，Prompt 结构化 JSON 输出                    |
| v1.2 | ChromaDB 风格 RAG                                            |
| v1.3 | LangGraph 串联 Vision → RAG → Generate                       |
| v1.4 | Streamlit 前端，流式输出，非商品图防幻觉                     |
| v2.0 | Hugging Face Spaces 首版部署                                 |
| v2.1 | FastAPI 网关层，前后端分离                                   |
| v2.2 | RAG 单例 + metadata 过滤 + Vision∥Retrieve 并行 + node timings |
| v2.3 | Redis 缓存（本地 Docker / Upstash）                          |
| v2.4 | 12 条规则评测 + Docker Compose 本地编排                      |
| v2.5 | `hf-clean`：HF 单容器 supervisord 重部署 + Upstash Redis 线上缓存 |

---

## 常见问题

**Q：HF 上第一次打开很慢？**
A：冷启动需构建 ChromaDB 向量库，约 1–2 分钟；之后会快很多。

**Q：Redis 连接失败怎么办？**
A：系统自动降级为直连 ChromaDB，不影响生成，仅检索稍慢。

**Q：为什么 RAG 范例有时和商品品类不完全匹配？**
A：当前 `styles.csv` 以服饰文案为主，潮玩/食品场景后续将扩充品类子库或分 collection。

**Q：100% 评测通过率说明什么？**
A：说明当前 Prompt + 流程在规则约束下稳定，属于回归测试，不是文案主观质量评分。

**Q：`main` 和 `hf-clean` 有什么区别？**  
A：`main` 面向本地开发与 Docker Compose；`hf-clean` 面向 HF Spaces 单端口约束，使用 supervisord 同容器运行 API + Streamlit，并配合 Upstash Redis。核心业务代码（`core/`、`api/`）两分支一致。

**Q：为什么 HF 用 7860 端口，本地用 8501？**  
A：HF Spaces 要求对外暴露 7860；本地 Streamlit 默认 8501。API 在两种环境下均监听容器/本机 8000，仅 Streamlit 对外端口不同。

---

## License

MIT

---

> Designed by [Daphne502](https://github.com/Daphne502) · 2026
