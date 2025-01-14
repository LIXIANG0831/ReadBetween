import os

from magic_pdf.data.data_reader_writer import S3DataReader, S3DataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# 替换为真实的 S3 桶名
bucket_name = "{Your S3 Bucket Name}"
# 替换为真实的 S3 访问密钥
ak = "{Your S3 access key}"
# 替换为真实的 S3 秘密密钥
sk = "{Your S3 secret key}"
# 替换为真实的 S3 终端节点 URL
endpoint_url = "{Your S3 endpoint_url}"

# 创建 S3 数据读取器，用于读取 S3 上的数据，需要替换 `unittest/tmp` 为真实的 S3 前缀
reader = S3DataReader('unittest/tmp/', bucket_name, ak, sk, endpoint_url)
# 创建 S3 数据写入器，用于将处理后的数据写入 S3
writer = S3DataWriter('unittest/tmp', bucket_name, ak, sk, endpoint_url)
# 创建用于写入图片的 S3 数据写入器
image_writer = S3DataWriter('unittest/tmp/images', bucket_name, ak, sk, endpoint_url)
# 创建用于写入 Markdown 文件的 S3 数据写入器
md_writer = S3DataWriter('unittest/tmp', bucket_name, ak, sk, endpoint_url)

# 本地图片目录和 Markdown 目录
local_image_dir, local_md_dir = "output/images", "output"
# 获取本地图片目录的名称
image_dir = str(os.path.basename(local_image_dir))

# 参数设置
# 替换为真实的 S3 路径
pdf_file_name = (
    f"s3://{bucket_name}/unittest/tmp/bug5-11.pdf"
)

# 准备环境
# 本地输出目录
local_dir = "output"
# 获取 PDF 文件名（不含后缀）
name_without_suff = os.path.basename(pdf_file_name).split(".")[0]

# 读取 PDF 文件内容
pdf_bytes = reader.read(pdf_file_name)  # 读取 PDF 文件内容

# 处理流程
## 创建数据集实例
ds = PymuDocDataset(pdf_bytes)

## 推理
if ds.classify() == SupportedPdfParseMethod.OCR:
    # 如果 PDF 需要使用 OCR 方法解析
    infer_result = ds.apply(doc_analyze, ocr=True)

    ## OCR 模式下的处理流程
    pipe_result = infer_result.pipe_ocr_mode(image_writer)

else:
    # 如果 PDF 不需要使用 OCR 方法解析
    infer_result = ds.apply(doc_analyze, ocr=False)

    ## 文本模式下的处理流程
    pipe_result = infer_result.pipe_txt_mode(image_writer)

### 在每一页上绘制模型结果
infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))

### 获取模型推理结果
model_inference_result = infer_result.get_infer_res()

### 在每一页上绘制布局结果
pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))

### 在每一页上绘制 span 结果
pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))

### 导出 Markdown 文件
pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)

### 导出内容列表
pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)

### 获取 Markdown 内容
md_content = pipe_result.get_markdown(image_dir)

### 获取内容列表内容
content_list_content = pipe_result.get_content_list(image_dir)

### 获取中间 JSON 数据
middle_json_content = pipe_result.get_middle_json()

### 导出中间 JSON 文件
pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')