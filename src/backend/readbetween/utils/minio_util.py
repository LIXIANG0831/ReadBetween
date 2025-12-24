import mimetypes
import os
import tempfile
from datetime import timedelta
from readbetween.config import settings
from readbetween.utils.logger_util import logger_util
from minio import Minio
from minio.error import S3Error

class MinioUtil:

    # 默认桶
    default_bucket_name = settings.storage.minio.default_bucket

    def __init__(self, endpoint=None, access_key=None, secret_key=None, secure=None):
        self.secure = secure or settings.storage.minio.secure
        self.endpoint = endpoint or settings.storage.minio.endpoint
        self.access_key = access_key or settings.storage.minio.access_key
        self.secret_key = secret_key or settings.storage.minio.secret_key
        self.client = Minio(self.endpoint, access_key=self.access_key, secret_key=self.secret_key, secure=self.secure)

    def bucket_exists(self, bucket_name: str) -> bool:
        """检查桶是否存在"""
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            logger_util.error(f"Error checking bucket existence: {e}")
            return False

    def create_bucket(self, bucket_name: str):
        """创建桶"""
        if not self.bucket_exists(bucket_name):
            try:
                self.client.make_bucket(bucket_name)
                logger_util.info(f"Bucket '{bucket_name}' created.")
            except S3Error as e:
                logger_util.error(f"Bucket创建失败:{e}")
                raise S3Error(code=500, message=f"Bucket创建失败:{e}")

    def upload_file(self, file_path: str, object_name: str, bucket_name: str = default_bucket_name, content_type: str = None):
        """上传文件到 MinIO"""
        try:
            if self.bucket_exists(bucket_name) is False:
                self.create_bucket(bucket_name)
            # 自动检测content_type
            if content_type is None:
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'  # 默认的二进制流类型
            with open(file_path, 'rb') as file_data:
                file_stat = os.stat(file_path)
                self.client.put_object(bucket_name, object_name, file_data, file_stat.st_size, content_type)
                logger_util.info(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
        except S3Error as e:
            logger_util.error(f"上传文件失败:{e}")
            raise S3Error(code=500, message=f"上传文件失败:{e}")

    def get_presigned_url(self, object_name: str, expires: int = 3600, bucket_name: str = default_bucket_name) -> str:
        """获取文件的预签名 URL"""
        try:
            return self.client.presigned_get_object(bucket_name, object_name, expires=timedelta(seconds=expires))
        except S3Error as e:
            logger_util.error(f"Error generating presigned URL: {e}")
            return ""

    def get_object_md5(self, object_name: str, bucket_name: str = default_bucket_name) -> str:
        """获取桶中对象的 MD5 值"""
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return stat.etag  # ETag 是对象的 MD5 值
        except S3Error as e:
            logger_util.error(f"Error getting MD5 for object '{object_name}' in bucket '{bucket_name}': {e}")
            return ""

    def download_file_to_temp(self, object_name: str, bucket_name: str = default_bucket_name, keep_extension: bool = True) -> str:
        """同步从 MinIO 下载文件到本地临时文件夹，并返回文件路径"""
        try:
            # 获取对象的元数据以了解文件类型
            stat = self.client.stat_object(bucket_name, object_name)
            content_type = stat.content_type if hasattr(stat, 'content_type') else None

            # 确定文件扩展名
            extension = ''
            if keep_extension:
                # 从对象名中提取扩展名
                if '.' in object_name:
                    extension = '.' + object_name.split('.')[-1]
                # 或者从content_type推断扩展名
                elif content_type:
                    extension = mimetypes.guess_extension(content_type) or ''
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
                # 下载文件
                self.client.fget_object(bucket_name, object_name, tmp_file.name)
                logger_util.info(f"File '{object_name}' downloaded to '{tmp_file.name}'.")
                return tmp_file.name
        except S3Error as e:
            logger_util.error(f"Error downloading file: {e}")
            return None

    def object_exists_by_md5(self, md5_value: str, bucket_name: str = default_bucket_name) -> (bool, str, str, str):
        """根据 MD5 值检查对象是否存在于桶中，如果存在，返回对象名和预签名 URL"""
        try:
            objects = self.client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                obj_stat = self.client.stat_object(bucket_name, obj.object_name)
                if obj_stat.etag.strip('"') == md5_value:
                    # 生成预签名 URL，固定过期时间为 1 小时
                    presigned_url = self.get_presigned_url(obj.object_name)
                    return True, obj.object_name, presigned_url
            return False, "", ""
        except S3Error as e:
            logger_util.error(f"Error checking object by MD5: {e}")
            return False, "", ""

    def set_bucket_policy_public(self, bucket_name: str):
        """设置桶策略为公共读取"""
        try:
            # MinIO 公共读取策略
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                    }
                ]
            }

            import json
            self.client.set_bucket_policy(bucket_name, json.dumps(policy))
            logger_util.info(f"Bucket '{bucket_name}' set to public read.")
            return True
        except S3Error as e:
            logger_util.error(f"Error setting bucket policy: {e}")
            return False

    def upload_file_get_permanent_url(self, file_path: str, object_name: str,
                                      bucket_name: str = "public",
                                      content_type: str = None,
                                      make_bucket_public: bool = True):
        """
        上传文件并返回永久可访问的URL

        Args:
            file_path: 本地文件路径
            object_name: 存储的对象名
            bucket_name: 桶名称
            content_type: 文件类型
            make_bucket_public: 是否设置桶为公共访问

        Returns:
            tuple: (成功标志, 永久URL, 对象名)
        """
        try:
            # 确保桶存在
            if not self.bucket_exists(bucket_name):
                self.create_bucket(bucket_name)

            # 设置桶为公共读取（如果需要）
            if make_bucket_public:
                self.set_bucket_policy_public(bucket_name)

            # 上传文件
            if content_type is None:
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'

            with open(file_path, 'rb') as file_data:
                file_stat = os.stat(file_path)
                self.client.put_object(bucket_name, object_name, file_data,
                                       file_stat.st_size, content_type)

            logger_util.info(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")

            # 生成永久URL
            permanent_url = self.get_permanent_url(object_name, bucket_name)

            return permanent_url

        except Exception as e:
            logger_util.error(f"上传文件失败: {e}")
            return None

    def get_permanent_url(self, object_name: str, bucket_name: str = "public") -> str:
        """
        获取文件的永久访问URL

        注意：这需要桶设置为公共读取权限
        """
        try:
            # 构建URL格式：http(s)://endpoint/bucket/object
            protocol = "https" if self.secure else "http"

            # 处理endpoint（移除http://或https://前缀）
            endpoint_clean = self.endpoint
            if endpoint_clean.startswith("http://"):
                endpoint_clean = endpoint_clean[7:]
            elif endpoint_clean.startswith("https://"):
                endpoint_clean = endpoint_clean[8:]

            # 移除端口后面的路径（如果有）
            endpoint_clean = endpoint_clean.split('/')[0]

            # 构建完整的URL
            permanent_url = f"{protocol}://{endpoint_clean}/{bucket_name}/{object_name}"

            return permanent_url

        except Exception as e:
            logger_util.error(f"Error generating permanent URL: {e}")
            return ""



# 使用示例
if __name__ == "__main__":
    minio_client = MinioUtil()
    bucket_name = 'test-minio'
    minio_client.create_bucket(bucket_name)

    # 上传文件
    minio_client.upload_file(bucket_name, './test.txt', 'uploads/file.txt')

    # 获取预签名 URL
    presigned_url = minio_client.get_presigned_url(bucket_name, 'uploads/file.txt')
    print(f"Presigned URL: {presigned_url}")
