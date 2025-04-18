import base64
import binascii
import json
import time
from typing import List, Dict, Optional
from DrissionPage._pages.session_page import SessionPage
import ast
from readbetween.settings import get_config
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import asyncio
import copy
import os
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine
from readbetween.core.context import file_open
from readbetween.utils.logger_util import logger_util


class BaseTool:
    @staticmethod
    def calculate_md5(file_path):
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class PdfExtractTool(BaseTool):
    def __init__(self, pdf_file, chunk_size=1000, repeat_size=200):
        self.pdf_file = pdf_file
        self.chunk_size = chunk_size
        self.repeat_size = repeat_size

    def extract(self):
        file_name = os.path.basename(self.pdf_file)
        results = []

        with file_open(self.pdf_file, 'rb') as file:

            chunk_bboxes = []
            chunk = ""  # chunk 内容
            repeat_chunk = ""  # 重叠内容
            chunk_index_cnt = 1  # 分片索引记数器

            for page_layout in extract_pages(file):
                page_number = page_layout.pageid
                for element in page_layout:
                    if len(chunk_bboxes) == 0:
                        start_page = page_number  # 记录chunk信息起始页
                    if isinstance(element, LTTextBox) or isinstance(element, LTTextLine):
                        text = element.get_text()
                        bbox = element.bbox
                        bbox_int = tuple(round(coord) for coord in bbox)
                        chunk += text
                        chunk_bboxes.append({
                            "page_no": page_number,
                            "bbox": list(bbox_int)
                        })
                        if len(chunk) >= self.chunk_size + self.repeat_size:
                            results.append({
                                "start_page": start_page,
                                "chunk_index": chunk_index_cnt,
                                "chunk_bboxes": chunk_bboxes,
                                "chunk": repeat_chunk + chunk,
                            })
                            chunk_index_cnt += 1
                            repeat_chunk = copy.deepcopy(chunk[self.repeat_size:])
                            chunk = ""
                            chunk_bboxes = []
            if len(chunk) > 0:
                results.append({
                    "start_page": start_page,
                    "chunk_index": chunk_index_cnt,
                    "chunk_bboxes": chunk_bboxes,
                    "chunk": repeat_chunk + chunk
                })
        return results


class EncryptionTool:
    def __init__(self):
        # 从配置中获取盐值并编码为字节
        self.SALT = self.get_salt().encode()
        # 生成密钥，使用盐值来增强安全性
        self.key = self.generate_key()
        self.cipher = Fernet(self.key)

    @staticmethod
    def get_salt() -> str:
        """从配置中获取盐值"""
        # 假设 get_config 是一个从配置文件中获取值的函数
        salt = get_config("extra.salt")
        if not salt:
            raise ValueError("Salt value is not configured. Please set the 'extra.salt' configuration.")
        return salt

    def generate_key(self) -> bytes:
        """生成基于盐的密钥"""
        # 使用 SHA-256 哈希函数生成密钥
        return base64.urlsafe_b64encode(hashlib.sha256(self.SALT).digest())

    def encrypt(self, password: str) -> str:
        """加密密码"""
        password_bytes = password.encode()
        encrypted_password = self.cipher.encrypt(password_bytes)
        # 返回加密后的数据，并确保使用 Base64 编码
        return encrypted_password.decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码"""
        try:
            # 尝试解密
            encrypted_bytes = encrypted_password.encode()
            decrypted_password = self.cipher.decrypt(encrypted_bytes)
            return decrypted_password.decode()
        except (InvalidToken, binascii.Error) as e:
            # 如果解密失败，记录错误日志并抛出异常
            logger_util.error(f"解密失败，加密数据可能已被篡改或密钥不匹配. 错误信息: {e}")
            raise ValueError(f"解密失败，加密数据可能已被篡改或密钥不匹配. 错误信息: {e}")

    def obscure(self, password: str) -> str:
        """模糊显示密码"""
        if len(password) < 13:
            return '*' * len(password)
        return password[:3] + '*' * 10 + password[13:]


BAIDU_ENDPOINT = "https://www.baidu.com/s"


class WebPage:
    """
    网页信息类，用于存储网页的基本信息，如标题、摘要、URL、来源和内容。
    """

    def __init__(self, name: str = "", snippet: str = "", url: str = "", source: str = "", content: str = ""):
        """
        初始化网页信息。

        :param name: 网页标题
        :param snippet: 网页摘要
        :param url: 网页URL
        :param source: 网页来源（如百度）
        :param content: 网页内容
        """
        self.name = name
        self.snippet = snippet
        self.url = url
        self.source = source
        self.content = content

    def to_dict(self) -> Dict:
        """
        将网页信息转换为字典格式，便于序列化。

        :return: 包含网页信息的字典
        """
        return {
            'name': self.name,
            'snippet': self.snippet,
            'content': self.content,
            'url': self.url,
            'source': self.source,
        }


class WebSearchTool:
    """
    网页搜索工具类，提供百度搜索和网页内容获取的功能。
    """

    @staticmethod
    def search_baidu(query: str, size: int = 10, lm: int = 3, tn: str = "news") -> List[WebPage]:
        """
        在百度上搜索指定的查询，并返回搜索结果页面的列表。

        :param query: 搜索关键词
        :param size: 返回结果的数量（默认10）
        :param lm: 搜索时间范围（默认3天）
        :param tn: 搜索类型（默认新闻）
        :return: 包含搜索结果的 WebPage 对象列表
        """
        try:
            # 构造百度搜索的URL
            url = f'{BAIDU_ENDPOINT}?wd={query}&rn={size}&lm={lm}&tn={tn}'
            page = SessionPage()
            time_out = 3
            # 发送请求获取页面内容
            page.get(url, timeout=time_out, retry=3, interval=0)
            if not page.html:
                logger_util.info("百度搜索异常, html为空")
                return []

            # 解析搜索结果
            elements = page.ele('#content_left').eles("tag:div@@class:result@@class:result@@class:new-pmd")
            pages = []
            for element in elements:
                try:
                    url = element.attr("mu")
                    name = element.ele("@href").text
                    snippet = element.text
                    if name and url and snippet:
                        # 创建 WebPage 对象并添加到结果列表
                        web_page = WebPage(name=name, snippet=snippet, content=snippet, url=url, source="baidu")
                        pages.append(web_page)
                except Exception as e:
                    logger_util.error(f"解析百度搜索结果时发生异常: {e}")
            return pages

        except Exception as e:
            logger_util.error(f"百度搜索发生异常: {e}")
            return []

    @staticmethod
    def get_page_detail(url: str, limit: int = 1000) -> Optional[str]:
        """
        获取指定URL的网页内容。

        :param url: 网页URL
        :param limit: 字符限制
        :return: 网页内容（截取前limit个字符），如果获取失败则返回None
        """
        start = time.time()
        try:
            page = SessionPage()
            # 发送请求获取网页内容
            page.get(url, timeout=1, retry=0, interval=0, show_errmsg=True)
            if page.html:
                # 提取网页正文内容
                body = page.ele("tag:body").text
                content = "。".join([item for item in body.split("\n") if len(item) > 0])
                if '�' not in content and len(content) > 50:
                    logger_util.info(f"获取网页内容成功，url: {url}，耗时：{time.time() - start}")
                    # 检查是否存在版权问题
                    if '授权' in content and '禁止使用' in content:
                        logger_util.error("版权问题，内容不可用")
                        return content[:limit]
                    else:
                        return content[:limit]
                else:
                    logger_util.error(f"内容异常不可用！content: {content}")
                    return None
            else:
                logger_util.error(f"获取网页详情失败，html为空，url: {url}, 耗时：{time.time() - start}")
        except Exception as e:
            logger_util.error(f"获取网页详情异常，url: {url}, 耗时：{time.time() - start}, 错误: {e}")
        return None


# 示例使用
if __name__ == "__main__":
    encryption_tool = EncryptionTool()  # 创建实例
    # 加密密码
    password = "你好"
    encrypted = encryption_tool.encrypt(password)
    print(f"Encrypted: {encrypted}")

    # 解密密码
    decrypted = encryption_tool.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")

    # PDF 解析
    # pdf_file_path = '/Users/lixiang/Documents/Test_Material/普通.pdf'
    # pdf_extract = PdfExtractTool(pdf_file_path)
    # results = asyncio.run(pdf_extract.extract())
    # for result in results:
    #     print(result)
    #     print("\n")

    # 示例：搜索百度并获取网页详情
    # search_tool = WebSearchTool()
    # results = search_tool.search_baidu('青岛的天气', size=5, lm=3)
    # detail_results = []

    # 遍历搜索结果，获取每个网页的详情
    # for result in results:
    #     detail_result = {"url": result.url, "title": result.name}
    #     content = search_tool.get_page_detail(result.url)
    #     if content:
    #         detail_result["content"] = content
    #         detail_results.append(detail_result)
    #
    # # 打印结果
    # print(json.dumps(detail_results, ensure_ascii=False, indent=4))
