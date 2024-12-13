import asyncio
import copy
import os
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine
from awsome.core.context import file_open


async def extract(pdf_file='/Users/lixiang/Documents/Test_Material/延长石油获过哪些荣誉.pdf', chunk_size=1000,
                  repeat_size=200):
    # 获取文件名
    file_name = os.path.basename(pdf_file)
    results = []
    chunk_bboxes = []
    chunk = ""  # chunk 内容
    repeat_chunk = ""  # 重叠内容
    # 打开PDF文件
    with file_open(pdf_file, 'rb') as file:
        # 使用extract_pages函数逐页提取页面
        for page_layout in extract_pages(file):
            # 获取页码
            page_number = page_layout.pageid
            # print(f'页码: {page_number}')
            # 打印页面中的文本信息
            for element in page_layout:
                if isinstance(element, LTTextBox) or isinstance(element, LTTextLine):
                    # 获取文本和边界框
                    text = element.get_text()
                    bbox = element.bbox
                    # 将bbox中的浮点数四舍五入到最接近的整数
                    bbox_int = tuple(round(coord) for coord in bbox)
                    # print(f'文本: {text}\n边界框: {bbox_int}')
                    chunk += text
                    chunk_bboxes.append({
                        "page_no": page_number,
                        "bbox": list(bbox_int)
                    })
                    if len(chunk) >= chunk_size + repeat_size:
                        results.append({
                            "chunk_bboxes": chunk_bboxes,
                            "chunk": file_name + ":" + repeat_chunk + chunk
                        })
                        # print(repeat_chunk + chunk)
                        repeat_chunk = copy.deepcopy(chunk[repeat_size:])
                        # print(repeat_chunk)
                        chunk = ""
            if len(chunk) > 0:
                results.append({
                    "chunk_bboxes": chunk_bboxes,
                    "chunk": repeat_chunk + chunk
                })
    return results


if __name__ == '__main__':
    results = asyncio.run(extract())
    print(results)
