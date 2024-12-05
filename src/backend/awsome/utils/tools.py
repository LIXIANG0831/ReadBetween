import base64
from awsome.settings import get_config
from cryptography.fernet import Fernet
import hashlib
import asyncio
import copy
import os
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine
from awsome.utils.context import file_open


class PdfExtractTool:
    def __init__(self, pdf_file, chunk_size=1000, repeat_size=200):
        self.pdf_file = pdf_file
        self.chunk_size = chunk_size
        self.repeat_size = repeat_size

    async def extract(self):
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
                                "chunk": file_name + ":" + repeat_chunk + chunk,
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
        self.SALT = get_config("extra.salt").encode()
        # 生成密钥，使用盐值来增强安全性
        self.key = self.generate_key()
        self.cipher = Fernet(self.key)

    def generate_key(self) -> bytes:
        """生成基于盐的密钥"""
        # 使用 SHA-256 哈希函数生成密钥
        return base64.urlsafe_b64encode(hashlib.sha256(self.SALT).digest())

    def encrypt(self, password: str) -> str:
        """加密密码"""
        password_bytes = password.encode()
        encrypted_password = self.cipher.encrypt(password_bytes)
        return encrypted_password.decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码"""
        encrypted_bytes = encrypted_password.encode()
        decrypted_password = self.cipher.decrypt(encrypted_bytes)
        return decrypted_password.decode()


# 示例使用
if __name__ == "__main__":
    # encryption_tool = EncryptionTool()  # 创建实例
    # 加密密码
    # password = "你好"
    # encrypted = encryption_tool.encrypt(password)
    # print(f"Encrypted: {encrypted}")

    # 解密密码
    # decrypted = encryption_tool.decrypt(encrypted)
    # print(f"Decrypted: {decrypted}")
    pdf_file_path = '/Users/lixiang/Documents/Test_Material/普通.pdf'
    pdf_extract = PdfExtractTool(pdf_file_path)
    results = asyncio.run(pdf_extract.extract())
    for result in results:
        print(result)
        print("\n")
