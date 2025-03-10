import importlib
import json
import os
from typing import Dict

import chardet
from langchain_unstructured import UnstructuredLoader  # 新导入
from langchain_community.document_loaders import JSONLoader, TextLoader

# 更新 LOADER_DICT，支持 UnstructuredLoader
LOADER_DICT = {
    "UnstructuredHTMLLoader": [".html", ".htm"],
    "MHTMLLoader": [".mhtml"],
    "TextLoader": [".md"],  # 保留 TextLoader 用于简单文本
    "UnstructuredMarkdownLoader": [".md"],
    "JSONLoader": [".json"],
    "JSONLinesLoader": [".jsonl"],
    "CSVLoader": [".csv"],
    "RapidOCRPDFLoader": [".pdf"],
    "RapidOCRDocLoader": [".docx"],
    "RapidOCRPPTLoader": [".ppt", ".pptx"],
    "RapidOCRLoader": [".png", ".jpg", ".jpeg", ".bmp"],
    "UnstructuredLoader": [  # 替换 UnstructuredFileLoader
        ".eml", ".msg", ".rst", ".rtf", ".txt", ".xml", ".epub", 
        ".odt", ".tsv", ".xlsx", ".xls", ".xlsd", ".ipynb", ".py",
        ".srt", ".toml", ".docx", ".ppt", ".pptx", ".enex"
    ],
    # 移除重复的专用加载器，统一使用 UnstructuredLoader
}

SUPPORTED_EXTS = [ext for sublist in LOADER_DICT.values() for ext in sublist]

def get_LoaderClass(file_extension):
    for LoaderClass, extensions in LOADER_DICT.items():
        if file_extension in extensions:
            return LoaderClass
    return None

def get_loader(loader_name: str, file_path: str, loader_kwargs: Dict = None):
    """
    根据loader_name和文件路径返回文档加载器。
    """
    loader_kwargs = loader_kwargs or {}
    try:
        if loader_name in [
            "RapidOCRPDFLoader", "RapidOCRLoader", "FilteredCSVLoader",
            "RapidOCRDocLoader", "RapidOCRPPTLoader"
        ]:
            document_loaders_module = importlib.import_module(
                "../../server/file_rag/document_loaders"
            )
        elif loader_name == "UnstructuredLoader":
            # 直接使用 langchain_unstructured
            DocumentLoader = UnstructuredLoader
        else:
            document_loaders_module = importlib.import_module(
                "langchain_community.document_loaders"
            )
            DocumentLoader = getattr(document_loaders_module, loader_name)
    except Exception as e:
        print(f"为文件{file_path}查找加载器{loader_name}时出错：{e}")
        DocumentLoader = UnstructuredLoader  # 默认回退到 UnstructuredLoader

    # 参数设置
    if loader_name == "UnstructuredLoader":
        loader_kwargs.setdefault("autodetect_encoding", True)
    elif loader_name == "CSVLoader":
        if not loader_kwargs.get("encoding"):
            with open(file_path, "rb") as struct_file:
                encode_detect = chardet.detect(struct_file.read())
            loader_kwargs["encoding"] = encode_detect.get("encoding", "utf-8")
    elif loader_name in ["JSONLoader", "JSONLinesLoader"]:
        loader_kwargs.setdefault("jq_schema", ".")
        loader_kwargs.setdefault("text_content", False)

    try:
        loader = DocumentLoader(file_path, **loader_kwargs)
        return loader
    except Exception as e:
        print(f"创建加载器{loader_name}失败：{e}")
        return UnstructuredLoader(file_path, **loader_kwargs)  # 回退方案