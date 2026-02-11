import streamlit as st
import os
import time
from PIL import Image
import shutil

try:
    from core.workflow import create_workflow
except ImportError:
    create_workflow = None

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
    /* 全局字体优化 */
    * { font-family: 'Inter', sans-serif !important; }
    
    /* 隐藏默认的菜单和页脚 */
    #MainMenu, footer, header { visibility: hidden; }

    /* 聊天气泡样式 */
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
    .user-bubble {
        background-color: #3B82F6;
        color: white;
        border-bottom-right-radius: 2px;
    }
    .bot-bubble {
        background-color: white;
        border: 1px solid #E5E7EB;
        color: #1F2937;
        border-bottom-left-radius: 2px;
    }

    /* 步骤条样式 */
    .step-box {
        padding: 10px; margin: 5px 0;
        background: #EFF6FF; border: 1px solid #BFDBFE;
        color: #1E40AF; border-radius: 8px; font-size: 13px;
    }
    .step-done {
        background: #F0FDF4; border: 1px solid #BBF7D0;
        color: #166534;
    }

    /* 底部固定栏样式 */
    .fixed-bottom {
        position: fixed; bottom: 0; left: 0; right: 0;
        background: white; padding: 20px;
        border-top: 1px solid #E5E7EB;
        z-index: 999;
        /* 这里预留左边距给侧边栏，防止遮挡 */
        padding-left: 22rem; 
    }
    /* 为了不被底部栏遮挡内容 */
    .main-content { padding-bottom: 150px; }
</style>
""", unsafe_allow_html=True)

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
    length_limit = st.slider("篇幅限制", 50, 1000, 300, step=50)
    
    st.markdown("---")
    # 动态提示，展示不同风格的特点
    tips = {
        "小红书种草": "特点：口语化、Emoji丰富、体验感强",
        "京东/淘宝电商": "特点：参数详实、功能点突出、甚至理性",
        "朋友圈私域": "特点：像朋友一样聊天、软植入、信任感",
        "抖音直播": "特点：短促有力、甚至有点紧迫感、引导下单"
    }
    st.info(tips[style_option])
    
    st.markdown("---")
    st.caption("Designed by Daphne502")

# 主区域：标题与消息展示
st.markdown('<div class="main-content">', unsafe_allow_html=True) # 开始内容包裹
st.title("E-ComMate Workspace")
st.markdown("上传商品图片，一键生成适配各平台的营销文案。")
st.divider()

# 如果没有消息，显示欢迎语
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
            if os.path.exists(msg["content"]):
                st.image(msg["content"], width=250)
    
    elif msg["type"] == "result":
        # 结果专门显示，带 Expander
        st.markdown(f"""
        <div class="chat-row bot-row">
            <div class="chat-bubble bot-bubble" style="width: 100%; max-width: 100%;">
                {msg["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
        # 你的“技术亮点”：折叠的调试信息
        with st.expander("查看 Vision 解析与参考数据 (Debug Info)"):
            st.json(msg.get("debug_data", {"info": "无调试数据"}))

# 核心生成逻辑 (带 Loading 动画)
if st.session_state.generating:
    st.session_state.generating = False # 重置状态
    
    # 占位符，用来显示进度动画
    status_placeholder = st.empty()
    
    try:
        with status_placeholder.container():
            st.markdown('<div class="step-box">正在分析商品视觉特征...</div>', unsafe_allow_html=True)
            time.sleep(0.8) # 模拟耗时，让动画被人看清
            
        with status_placeholder.container():
            st.markdown('<div class="step-box step-done">视觉分析完成</div>', unsafe_allow_html=True)
            st.markdown('<div class="step-box">正在检索相似爆款文案 (RAG)...</div>', unsafe_allow_html=True)
            time.sleep(0.8)

        with status_placeholder.container():
            st.markdown('<div class="step-box step-done">视觉分析完成</div>', unsafe_allow_html=True)
            st.markdown('<div class="step-box step-done">RAG 检索完成</div>', unsafe_allow_html=True)
            st.markdown('<div class="step-box">正在撰写最终文案...</div>', unsafe_allow_html=True)
            time.sleep(0.8)
            
            final_copy = ""
            debug_info = {}
            
            if create_workflow:
                app = create_workflow()
                inputs = {
                    "image_path": st.session_state.temp_img_path,
                    "user_style": style_option,
                    "words_limit": length_limit,
                    "image_data": {}, 
                    "retrieved_examples": [],
                    "final_copy": ""
                }
                res = app.invoke(inputs)
                final_copy = res.get("final_copy", "生成出错")
                debug_info = {
                    "vision_tags": res.get("image_data", {}),
                    "references": res.get("retrieved_examples", [])
                }
            else:
                # 保底 Mock
                final_copy = f"【{style_option}】这里是生成的文案内容...\n\n这款产品真的非常不错，适合夏天使用！"
                debug_info = {"tag": "demo_mode", "confidence": 0.98}

        status_placeholder.empty() # 清除进度条

        # 存入历史并刷新
        st.session_state.messages.append({
            "role": "bot", 
            "type": "result", 
            "content": final_copy,
            "debug_data": debug_info
        })
        st.rerun()

    except Exception as e:
        status_placeholder.empty()
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
    
    # 只有当文件是新上传的时候才处理
    if "temp_img_path" not in st.session_state or st.session_state.temp_img_path != file_path:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.temp_img_path = file_path
        # 把图片加入聊天记录
        st.session_state.messages.append({
            "role": "user", "type": "image", "content": file_path
        })
        st.rerun()

if start_btn:
    if "temp_img_path" not in st.session_state:
        st.toast("请先上传一张图片！") # 用 Toast 提示更像原生 App
    else:
        st.session_state.generating = True
        st.session_state.messages.append({
            "role": "user", 
            "type": "text", 
            "content": f"帮我写一份 {style_option} 的文案，大约 {length_limit} 字。"
        })
        st.rerun()
        
if os.path.exists("temp"):
    shutil.rmtree("temp")