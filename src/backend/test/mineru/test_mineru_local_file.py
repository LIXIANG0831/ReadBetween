import os

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# 参数
pdf_file_name = "abc.pdf"  # 替换为真实的 pdf 路径
name_without_suff = pdf_file_name.split(".")[0]

print(name_without_suff)

# 准备环境
local_image_dir, local_md_dir = "output/images", "output"
image_dir = str(os.path.basename(local_image_dir))

os.makedirs(local_image_dir, exist_ok=True)

image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

# 读取字节
reader1 = FileBasedDataReader("")
pdf_bytes = reader1.read(pdf_file_name)  # 读取 pdf 内容

# 处理
## 创建数据集实例
ds = PymuDocDataset(pdf_bytes)

## 推理
if ds.classify() == SupportedPdfParseMethod.OCR:
    infer_result = ds.apply(doc_analyze, ocr=True)

    ## ocr 模式管道
    pipe_result = infer_result.pipe_ocr_mode(image_writer)

else:
    infer_result = ds.apply(doc_analyze, ocr=False)

    ## 文本模式管道
    pipe_result = infer_result.pipe_txt_mode(image_writer)

### 在每一页上绘制模型结果
infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))

### 获取模型推理结果
model_inference_result = infer_result.get_infer_res()

### 在每一页上绘制布局结果
pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))

### 在每一页上绘制 spans 结果
pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))

### 获取 markdown 内容
md_content = pipe_result.get_markdown(image_dir)

### 写入 markdown
pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)

### 获取内容列表内容
content_list_content = pipe_result.get_content_list(image_dir)

### 写入内容列表
pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)

### 获取中间 json
middle_json_content = pipe_result.get_middle_json()

### 写入中间 json
pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')