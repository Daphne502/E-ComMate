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
# NinthCommit: <style>内第一行不再使用 * 强制覆盖，确保 Streamlit 的图标字体能正常渲染
st.markdown("""
<style>
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
        background: white; padding: 10px 20px 30px 21rem;
        border-top: 1px solid #E5E7EB;
        z-index: 999;
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
    
    # refactor: 增加“清空对话”按钮
    if st.button("清空所有对话", use_container_width=True):
        st.session_state.messages = []
        # 清理可能存在的临时路径状态
        if "temp_img_path" in st.session_state:
            del st.session_state.temp_img_path
        st.rerun()

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
        # EighthCommit: 进入生成前，先检查并恢复临时文件，确保图片复用性
        if not os.path.exists(st.session_state.temp_img_path):
            last_image_bytes = next((msg["content"] for msg in reversed(st.session_state.messages) if msg["type"] == "image"), None)
            if last_image_bytes:
                with open(st.session_state.temp_img_path, "wb") as f:
                    f.write(last_image_bytes)
    
        # EighthCommit：简化 st.status 的使用，避免状态框文字堆叠
        # 不再频繁使用 state="error" 等参数，直接通过 label 更新状态           
        with st.status("正在处理中...", expanded=True) as status:
            st.write("正在分析商品特征...")
            
            status.update(label="正在分析视觉特征...")
            time.sleep(0.5) 
            
            status.update(label="正在检索参考范例...")
            time.sleep(0.5)
            
            status.update(label="正在撰写最终文案...")
            
            if create_workflow:
                app = create_workflow()
                inputs = {
                    "image_path": st.session_state.temp_img_path,
                    "user_style": style_option,
                    "words_limit": str(length_limit),
                    "user_note": st.session_state.get("current_user_note", ""), # 传给 Agent
                    "image_data": {}, 
                    "retrieved_examples": [],
                    "final_copy": ""
                }
                res = app.invoke(inputs)
                
                # EighthCommit：移除“识别失败”的硬报错
                image_data = res.get("image_data", {})
                final_copy = res.get("final_copy", "生成出错")
                debug_info = {
                    "vision_analysis": image_data,
                    "rag_references": res.get("retrieved_examples", [])
                }
            else:
                time.sleep(1)
                final_copy = "这是演示文案..."
                debug_info = {"info": "Demo Mode"}
                
            # SeventhCommit: 任务完成,更新状态框为完成并折叠
            status.update(label="文案生成完毕！", expanded=False)

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
            "content": full_text, 
            "debug_data": debug_info
        })

        if os.path.exists(st.session_state.temp_img_path):
            os.remove(st.session_state.temp_img_path)

        # SeventhCommit：删除之前为 DOM 缓冲留的 0.8s 睡眠时间，让体验更顺滑
        st.rerun()

    except Exception as e:
        st.error(f"运行出错: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# 底部固定交互区
st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
with st.container():
    c1, c2 = st.columns([4, 1])

with c1:
    uploaded_file = st.file_uploader("上传图片", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    # refactor: 补充需求输入框
    user_note = st.text_input("有什么特别想强调的吗？", placeholder="例如：突出8折优惠、纯棉材质、送礼首选...", label_visibility="collapsed")
    
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
        st.session_state.messages.append({"role": "user", "type": "image", "content": image_bytes})
        st.rerun()

if start_btn:
    if "temp_img_path" not in st.session_state:
        st.toast("请先上传一张图片！") 
    else:
        st.session_state.generating = True
        st.session_state.current_user_note = user_note
        st.session_state.messages.append({
            "role": "user", 
            "type": "text", 
            "content": f"要求：{style_option}，约{length_limit}字。备注：{user_note if user_note else '无'}"
        })
        st.rerun()