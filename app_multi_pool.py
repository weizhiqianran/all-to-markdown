import streamlit as st
import os
from concurrent.futures import ThreadPoolExecutor
from utils import get_loader, get_LoaderClass, SUPPORTED_EXTS
from PIL import Image
import io

# 检查文件完整性（针对图片）
def check_image_integrity(file_content):
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()  # 验证图像完整性
        return True
    except Exception:
        return False

# 处理单个文件的函数
def process_file(uploaded_file, index, total):
    file_path = os.path.join("temp", uploaded_file.name)
    result_container = st.empty()  # 用于动态更新状态
    try:
        # 保存文件并检查完整性
        file_content = uploaded_file.getbuffer()
        if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            if not check_image_integrity(file_content):
                return f"文件 {uploaded_file.name} 已损坏或截断", None
                
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        loader_name = get_LoaderClass(file_extension)
        
        if not loader_name:
            return f"不支持的文件类型: {file_extension}", None
            
        # 更新状态
        result_container.info(f"正在处理文件 {uploaded_file.name} ({index+1}/{total})...")
        
        loader = get_loader(loader_name, file_path)
        documents = loader.load()
        return None, (uploaded_file.name, documents)
        
    except Exception as e:
        return f"处理文件 {uploaded_file.name} 时出错: {e}", None
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# 主程序
st.title("文件上传与内容分析")

uploaded_files = st.file_uploader(
    "Choose files",
    type=SUPPORTED_EXTS,
    accept_multiple_files=True
)

if uploaded_files:
    os.makedirs("temp", exist_ok=True)
    
    progress_bar = st.progress(0)
    results = []
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=4) as executor:  # 限制最大线程数
        futures = [
            executor.submit(process_file, file, i, len(uploaded_files))
            for i, file in enumerate(uploaded_files)
        ]
        
        # 收集结果并更新进度
        for i, future in enumerate(futures):
            error, result = future.result()
            if error:
                st.error(error)
            elif result:
                results.append(result)
            progress_bar.progress((i + 1) / len(uploaded_files))
    
    # 显示处理结果
    for name, documents in results:
        st.subheader(f"文件内容 - {name}")
        for doc in documents:
            st.write(doc.page_content)
            st.write("元数据:", doc.metadata)
    
    # 清理临时目录
    if os.path.exists("temp") and not os.listdir("temp"):
        os.rmdir("temp")