import copy
import os
import tempfile
import uuid
from typing import List
from pathlib import Path
from abc import ABC, abstractmethod

from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader
)
from langchain.docstore.document import Document
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTImage, LTFigure, LTTextBox, LTTextLine

from readbetween.utils.logger_util import logger_util
from readbetween.utils.minio_util import MinioUtil


class BaseFileSplitter(ABC):
    """基础文件分割器接口"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
            length_function=len,
        )

    @abstractmethod
    def load_and_split(self, file_path: str) -> List[Document]:
        """加载并分割文件"""
        pass

    def _post_process_chunks(self, chunks: List[Document]) -> List[Document]:
        """后处理chunks，添加元数据"""
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            })
            processed_chunks.append(chunk)
        return processed_chunks


class PDFSplitterWrapper(BaseFileSplitter):
    """PDF文件分割器"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, is_embed_image: bool = False):
        # 调用父类初始化
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        # 是否将图片加入分片
        self.is_embed_image = is_embed_image
        # 初始化MinioUtil
        self.minio_util = MinioUtil()
        logger_util.info("PDFSplitterWrapper: MinioUtil初始化完成")

    def _handle_figure(self, element: LTImage | LTFigure, page_number, file_name=None):
        """处理LTFigure元素（可能包含图片）"""
        if isinstance(element, LTImage):
            # 保存图片
            image_data = element.stream.get_data()
            if file_name is None:
                file_name = f"page{page_number:06d}_img_{uuid.uuid4().hex}.png"
            else:
                file_name = f"{file_name}_page{page_number:06d}_img_{uuid.uuid4().hex}.png"
            object_name = f"knowledge_image/{file_name}"
            ext = Path(file_name).suffix

            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext if ext else '.tmp') as tmp_file:
                tmp_file.write(image_data)
                tmp_path = tmp_file.name
                try:
                    try:
                        image_url = self.minio_util.upload_file_get_permanent_url(tmp_path, object_name)
                        return image_url if image_url is not None else ""
                    except Exception as e:
                        logger_util.error(f"上传图片到MinIO失败: {e}")
                        return ""
                finally:
                    # 确保临时文件被删除
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger_util.debug(f"临时文件已删除: {tmp_path}")

        for sub_element in element:
            if isinstance(sub_element, LTImage):
                # 递归处理image
                return self._handle_figure(sub_element, page_number, file_name)
            elif isinstance(sub_element, LTFigure):
                # 递归处理嵌套的figure
                return self._handle_figure(sub_element, page_number, file_name)
        return ""

    def load_and_split(self, file_path: str) -> List[Document]:
        try:
            # loader = PyPDFLoader(file_path)
            # documents = loader.load()
            #
            # # 添加文件类型元数据
            # for doc in documents:
            #     doc.metadata["file_type"] = "pdf"
            #     doc.metadata["file_path"] = file_path
            #
            # chunks = self.text_splitter.split_documents(documents)
            # return self._post_process_chunks(chunks)

            pdf_chunks: List[Document] = []
            from readbetween.core.context import file_open
            from readbetween.utils.tools import BaseTool
            with file_open(file_path, 'rb') as file:

                chunk_bboxes = []
                chunk = ""  # chunk 内容
                repeat_chunk = ""  # 重叠内容

                for page_layout in extract_pages(file):
                    page_number = page_layout.pageid
                    for element in page_layout:
                        if len(chunk_bboxes) == 0:
                            start_page = page_number  # 记录chunk信息起始页

                        # 判断是否将图片加入分片
                        if self.is_embed_image is True:
                            # 检查是否是图片
                            if isinstance(element, LTImage) or isinstance(element, LTFigure):
                                bbox = element.bbox
                                bbox_int = tuple(round(coord) for coord in bbox)
                                # 图片上传OSS返回图片链接
                                images_url = self._handle_figure(element, page_number, None)
                                images_url = BaseTool.format_md_image_url(images_url)
                                chunk += f"{images_url}\n"
                                chunk_bboxes.append({
                                    "page_no": page_number,
                                    "bbox": list(bbox_int)
                                })

                        if isinstance(element, LTTextBox) or isinstance(element, LTTextLine):
                            text = element.get_text()
                            bbox = element.bbox
                            bbox_int = tuple(round(coord) for coord in bbox)
                            chunk += text
                            chunk_bboxes.append({
                                "page_no": page_number,
                                "bbox": list(bbox_int)
                            })
                            if len(chunk) >= self.chunk_size + self.chunk_overlap:
                                new_doc = Document(page_content=repeat_chunk + chunk)
                                # 添加元数据
                                new_doc.metadata["page"] = start_page
                                new_doc.metadata["chunk_bboxes"] = chunk_bboxes
                                new_doc.metadata["file_type"] = "pdf"
                                new_doc.metadata["file_path"] = file_path
                                new_doc.metadata["source"] = file_path

                                pdf_chunks.append(new_doc)
                                repeat_chunk = copy.deepcopy(chunk[self.chunk_overlap:])
                                chunk = ""
                                chunk_bboxes = []
                if len(chunk) > 0:
                    new_doc = Document(page_content=repeat_chunk + chunk)
                    # 添加元数据
                    new_doc.metadata["page"] = start_page
                    new_doc.metadata["chunk_bboxes"] = chunk_bboxes
                    new_doc.metadata["file_type"] = "pdf"
                    new_doc.metadata["file_path"] = file_path
                    new_doc.metadata["source"] = file_path

                    pdf_chunks.append(new_doc)

            return self._post_process_chunks(pdf_chunks)

        except Exception as e:
            logger_util.error(f"PDF文件处理失败: {file_path}, 错误: {str(e)}")
            raise


class WordSplitterWrapper(BaseFileSplitter):
    """Word文档分割器"""

    def load_and_split(self, file_path: str) -> List[Document]:
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()

            # 添加文件类型元数据
            for doc in documents:
                doc.metadata["file_type"] = "word"
                doc.metadata["file_path"] = file_path

            chunks = self.text_splitter.split_documents(documents)
            return self._post_process_chunks(chunks)
        except Exception as e:
            logger_util.error(f"Word文件处理失败: {file_path}, 错误: {str(e)}")
            raise


class TextSplitterWrapper(BaseFileSplitter):
    """文本文件分割器"""

    def load_and_split(self, file_path: str) -> List[Document]:
        try:
            encoding = self._detect_encoding(file_path)
            loader = TextLoader(file_path, encoding=encoding)
            documents = loader.load()

            # 添加文件类型元数据
            for doc in documents:
                doc.metadata["file_type"] = "text"
                doc.metadata["file_path"] = file_path
                doc.metadata["encoding"] = encoding

            chunks = self.text_splitter.split_documents(documents)
            return self._post_process_chunks(chunks)
        except Exception as e:
            logger_util.error(f"文本文件处理失败: {file_path}, 错误: {str(e)}")
            raise

    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'  # 默认使用utf-8


class UnifiedFileSplitter:
    """统一文件分割器，根据文件类型自动选择对应的分割器"""

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 is_embed_image: bool = False):
        """
        初始化统一文件分割器

        Args:
            chunk_size: 分片大小
            chunk_overlap: 分片重叠大小
            is_embed_image: 是否嵌入图片（仅对PDF有效）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.is_embed_image = is_embed_image

        # 注册支持的文件类型和对应的分割器
        self.splitter_registry = {
            '.pdf': self._create_pdf_splitter,
            '.doc': self._create_word_splitter,
            '.docx': self._create_word_splitter,
            '.txt': self._create_text_splitter,
            '.text': self._create_text_splitter,
            '.md': self._create_text_splitter,
            '.markdown': self._create_text_splitter,
        }

    def _create_pdf_splitter(self) -> PDFSplitterWrapper:
        """创建PDF分割器"""
        return PDFSplitterWrapper(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            is_embed_image=self.is_embed_image
        )

    def _create_word_splitter(self) -> WordSplitterWrapper:
        """创建Word分割器"""
        return WordSplitterWrapper(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def _create_text_splitter(self) -> TextSplitterWrapper:
        """创建文本分割器"""
        return TextSplitterWrapper(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名（小写）"""
        return Path(file_path).suffix.lower()

    def get_splitter(self, file_path: str) -> BaseFileSplitter:
        """
        根据文件路径获取对应的分割器

        Args:
            file_path: 文件路径

        Returns:
            BaseFileSplitter: 对应的文件分割器实例

        Raises:
            ValueError: 不支持的文件类型
        """
        file_ext = self.get_file_extension(file_path)

        if file_ext not in self.splitter_registry:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        return self.splitter_registry[file_ext]()

    def load_and_split(self,
                       file_path: str,
                       chunk_size: int = None,
                       chunk_overlap: int = None,
                       is_embed_image: bool = None) -> List[Document]:
        """
        加载并分割文件

        Args:
            file_path: 文件路径
            chunk_size: 分片大小（可选，覆盖初始化时的设置）
            chunk_overlap: 分片重叠大小（可选，覆盖初始化时的设置）
            is_embed_image: 是否嵌入图片（可选，覆盖初始化时的设置）

        Returns:
            List[Document]: 分割后的文档列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件类型
            Exception: 文件处理失败
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 如果提供了覆盖参数，更新实例参数
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        if is_embed_image is not None:
            self.is_embed_image = is_embed_image

        # 获取对应的分割器
        splitter = self.get_splitter(file_path)

        # 调用分割器的load_and_split方法
        return splitter.load_and_split(file_path)


if __name__ == '__main__':
    unified_splitter = UnifiedFileSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        is_embed_image=False
    )

    files = [
        '/Users/lixiang/Documents/Test_Material/OSU俄亥俄州立大学.pdf',
        '/Users/lixiang/Documents/Test_Material/OSU俄亥俄州立大学.docx',
        '/Users/lixiang/Documents/Test_Material/llm.txt'
    ]

    for file in files:
        chunks = unified_splitter.load_and_split(file)
        for chunk in chunks:
            print("=====")
            print(chunk)
            print("=====")
