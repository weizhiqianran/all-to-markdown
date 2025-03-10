import streamlit as st
import os
from utils import get_loader, get_LoaderClass, SUPPORTED_EXTS


# Streamlit 页面标题
st.title("文件上传与内容分析")

# 文件上传控件
uploaded_files = st.file_uploader(
    "Choose files", 
    type=SUPPORTED_EXTS,
    accept_multiple_files=True
)

if uploaded_files:

    os.makedirs("temp", exist_ok=True)
        
    for uploaded_file in uploaded_files:
            # Save uploaded file to temporary path
            file_path = os.path.join("temp", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # 获取文件扩展名
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            # 根据扩展名获取加载器类名
            loader_name = get_LoaderClass(file_extension)
            if not loader_name:
                st.error(f"不支持的文件类型: {file_extension}")
            else:
                try:
                    # 获取加载器实例
                    loader = get_loader(loader_name, file_path)
                    
                    # 加载文件内容
                    documents = loader.load()
                    
                    # 显示文件内容
                    st.subheader("文件内容")
                    for doc in documents:
                        st.write(doc.page_content)
                        st.write("元数据:", doc.metadata)
                except Exception as e:
                    st.error(f"处理文件时出错: {e}")
                
                # 清理临时文件
                os.remove(file_path)

# 清理临时目录（可选）
if os.path.exists("temp") and not os.listdir("temp"):
    os.rmdir("temp")