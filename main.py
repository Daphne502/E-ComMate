import streamlit as st
import os
import time
from PIL import Image

from core.workflow import create_workflow

# 基础页面配置
st.set_page_config(
    page_title="E-ComMate",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式
st.markdown("""
<style>
    * { font-family: 'Inter', sans-serif !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .chat-row { display: flex; margin-bottom: 20px; }
    .user-row { justify-content: flex-end; }
    .bot-row { justify-content: flex-start; }
    .chat-bubble {
        padding: 15px 20px;
        border-radius: 12px;
        max-width: 75%;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .user-bubble { background-color: #3B82F6; color: white; border-bottom-right-radius: 2px; }
    .bot-bubble { background-color: white; border: 1px solid #E5E7EB; color: #1F2937; border-bottom-left-radius: 2px; }
    .step-box {
        padding: 10px; margin: 5px 0;
        background: #EFF6FF; border: 1px solid #BFDBFE;
        color: #1E40AF; border-radius: 8px; font-size: 13px;
    }
    .step-done { background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; }
    .fixed-bottom {
        position: fixed; bottom: 0; left: 0; right: 0;
        background: white; padding: 20px;
        border-top: 1px solid #E5E7EB;
        z-index: 999;
        padding-left: 22rem; 
    }
    .main-content { padding-bottom: 150px; }
</style>
""", unsafe_allow_html=True)

# SixthCommit新增修改: 流式输出模拟器
def stream_text_simulator(text):
    for word in text:
        yield word
        time.sleep(0.02)
        
# 初始化状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generating" not in st.session_state:
    st.session_state.generating = False

# 侧边栏设置
with st.sidebar:
    st.header("E-ComMate")
    st.caption("智能电商文案助手")
    
    st.markdown("---")
    style_option = st.selectbox("文案风格", ["小红书种草", "京东/淘宝电商", "朋友圈私域", "抖音直播"])
    length_limit = st.slider("篇幅限制", 0, 300, 100, step=20)
    
    st.markdown("---")
    tips = {
        "小红书种草": "特点：强互动感、Emoji丰富、体验感强",
        "京东/淘宝电商": "特点：参数详实、功能点突出、甚至理性",
        "朋友圈私域": "特点：像朋友一样聊天、软植入、信任感",
        "抖音直播": "特点：短促有力、甚至有点紧迫感、引导下单"
    }
    st.info(tips[style_option])
    
    st.markdown("---")
    st.caption("Designed by Daphne502")

# 主区域：标题与消息展示
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.title("E-ComMate Workspace")
st.markdown("上传商品图片，一键生成适配各平台的营销文案。")
st.divider()

if not st.session_state.messages:
    st.markdown("""
    <div class="chat-row bot-row">
        <div class="chat-bubble bot-bubble">
            你好！我是你的文案助手。请在底部上传一张商品图，我来帮你写文案。
        </div>
    </div>
    """, unsafe_allow_html=True)

# 遍历并显示历史消息
for msg in st.session_state.messages:
    if msg["type"] == "text":
        # 区分 User 和 Bot 的样式
        row_cls = "user-row" if msg["role"] == "user" else "bot-row"
        bubble_cls = "user-bubble" if msg["role"] == "user" else "bot-bubble"
        st.markdown(f"""
        <div class="chat-row {row_cls}">
            <div class="chat-bubble {bubble_cls}">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
    elif msg["type"] == "image":
        # 图片专门显示
        col1, col2 = st.columns([1, 4])
        with col2:
            # SeventhCommit：兼容读取字节流(bytes)或本地路径。使用字节流摆脱对本地 temp 图片的依赖
            if isinstance(msg["content"], bytes):
                st.image(msg["content"], width=250)
            elif isinstance(msg["content"], str) and os.path.exists(msg["content"]):
                st.image(msg["content"], width=250)
    
    elif msg["type"] == "result":
        st.markdown(f"""
        <div class="chat-row bot-row">
            <div class="chat-bubble bot-bubble" style="width: 100%; max-width: 100%;">
                {msg["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
        # 折叠的调试信息
        with st.expander("查看 Vision 解析与参考数据 (Debug Info)"):
            st.json(msg.get("debug_data", {"info": "无调试数据"}))

# 核心生成逻辑 (修改了流式输出和校验)
if st.session_state.generating:
    st.session_state.generating = False
    
    # SeventhCommit: 废弃手动控制的 st.empty() 进度条，改为 Streamlit 原生的 st.status()
        # 彻底解决频繁操作 DOM 树导致流式输出触发 removeChild 报错的问题
  
    try:
        with st.status("正在分析商品特征与检索爆款...", expanded=True) as status:
            st.write("正在分析商品视觉特征...")
            time.sleep(0.8) # 模拟 Vision 模型耗时
            
            st.write("正在检索相似爆款文案 (RAG)...")
            time.sleep(0.8)
            
            st.write("正在撰写最终文案...")
            time.sleep(0.8)
            
            final_copy = ""
            debug_info = {}
            
            if create_workflow:
                app = create_workflow()
                inputs = {
                    "image_path": st.session_state.temp_img_path,
                    "user_style": style_option,
                    "words_limit": str(length_limit),
                    "image_data": {}, 
                    "retrieved_examples": [],
                    "final_copy": ""
                }
                res = app.invoke(inputs)
                # [真实] 商品图校验逻辑
                image_data = res.get("image_data", {})
                description = image_data.get("description", "")
                is_invalid = (not description) or ("未知商品" in description)
                
                if is_invalid:
                    # SeventhCommit: 校验失败时更新状态框
                    status.update(label="识别失败", state="error", expanded=True)
                    st.error("识别失败：这似乎不是一张商品图，或者图片无法解析。")
                    st.session_state.messages.append({
                        "role": "bot", "type": "text", 
                        "content": "图片解析失败，请上传主体清晰的商品图片重试。"
                    })
                    
                    # SeventhCommit：解析失败，直接清理 temp 临时文件
                    if os.path.exists(st.session_state.temp_img_path):
                        try:
                            os.remove(st.session_state.temp_img_path)
                        except Exception as e:
                            print(f"清理临时文件失败: {e}")
                            
                    time.sleep(1) 
                    st.rerun()
                
                final_copy = res.get("final_copy", "生成出错")
                debug_info = {
                    "vision_analysis": image_data,
                    "rag_references": res.get("retrieved_examples", [])
                }
            else:
                time.sleep(2)
                final_copy = "这是演示文案..."
                debug_info = {"info": "Demo Mode"}
                
            # SeventhCommit: 任务完成,更新状态框为完成并折叠
            status.update(label="文案生成完毕！", state="complete", expanded=False)

        # SeventhCommit：删除了 `time.sleep(6)` 和 `status_placeholder.empty()`，st.status 自己会处理好 DOM 渲染
        result_container = st.chat_message("assistant", avatar="🛍️")
        response_stream = stream_text_simulator(final_copy)
        # SixthCommit新增修改
        full_text = result_container.write_stream(response_stream)
           
        
        # [SixthCommit新增/修改逻辑]: 渲染完成后直接在这里显示调试信息
        with st.expander("查看 Vision 解析与参考数据 (Debug Info)"):
            st.json(debug_info)
            
        # 存入历史并刷新   
        st.session_state.messages.append({
            "role": "bot", 
            "type": "result", 
            "content": full_text, # 存入完整的文案文本
            "debug_data": debug_info
        })
        # SeventhCommit：正常跑完流程后，彻底删除本地的 temp 图片，实现随用随删。
        if os.path.exists(st.session_state.temp_img_path):
            try:
                os.remove(st.session_state.temp_img_path)
            except Exception as e:
                print(f"清理临时文件失败: {e}")
        
        # SeventhCommit：删除之前为 DOM 缓冲留的 0.8s 睡眠时间，让体验更顺滑
        st.rerun()

    except Exception as e:
        st.error(f"运行出错: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True) # 结束内容包裹

# 底部固定交互区
st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])

with c1:
    uploaded_file = st.file_uploader("上传图片", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

with c2:
    st.markdown("<br>", unsafe_allow_html=True) 
    start_btn = st.button("开始生成", use_container_width=True, type="primary")

st.markdown('</div>', unsafe_allow_html=True)

# 处理上传和点击事件
if uploaded_file:
    # 保存文件
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", uploaded_file.name)
    
    # SeventhCommit：在这里定义 image_bytes
    image_bytes = uploaded_file.getvalue()
    
    # 只有当文件是新上传的时候才处理
    if "temp_img_path" not in st.session_state or st.session_state.temp_img_path != file_path:
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        st.session_state.temp_img_path = file_path
        
        # SeventhCommit：存入聊天记录的是字节流(image_bytes)而非本地路径。这样哪怕后面 `os.remove()` 删了硬盘里的图片，聊天界面的历史记录也照样能渲染出来
        st.session_state.messages.append({
            "role": "user", "type": "image", "content": image_bytes
        })
        st.rerun()

if start_btn:
    if "temp_img_path" not in st.session_state:
        st.toast("请先上传一张图片！") 
    else:
        st.session_state.generating = True
        st.session_state.messages.append({
            "role": "user", 
            "type": "text", 
            "content": f"帮我写一份 {style_option} 的文案，大约 {length_limit} 字。"
        })
        st.rerun()