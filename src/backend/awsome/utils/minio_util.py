import os
from datetime import timedelta
from awsome.settings import get_config
from awsome.utils.logger_util import logger_util
from minio import Minio
from minio.error import S3Error

class MinioClient:

    # 默认桶
    default_bucket_name = get_config("storage.minio.default_bucket")

    def __init__(self, endpoint=None, access_key=None, secret_key=None, secure=None):
        secure = secure or get_config("storage.minio.secure")
        endpoint = endpoint or get_config("storage.minio.minio_endpoint")
        access_key = access_key or get_config("storage.minio.minio_access_key")
        secret_key = secret_key or get_config("storage.minio.minio_secret_key")
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

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
                logger_util.error(f"Error creating bucket: {e}")

    def upload_file(self, file_path: str, object_name: str, bucket_name: str = default_bucket_name):
        """上传文件到 MinIO"""
        try:
            with open(file_path, 'rb') as file_data:
                file_stat = os.stat(file_path)
                self.client.put_object(bucket_name, object_name, file_data, file_stat.st_size)
                logger_util.info(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
        except S3Error as e:
            logger_util.error(f"Error uploading file: {e}")

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





# 使用示例
if __name__ == "__main__":
    minio_client = MinioClient()
    bucket_name = 'test-minio'
    minio_client.create_bucket(bucket_name)

    # 上传文件
    minio_client.upload_file(bucket_name, './test.txt', 'uploads/file.txt')

    # 获取预签名 URL
    presigned_url = minio_client.get_presigned_url(bucket_name, 'uploads/file.txt')
    print(f"Presigned URL: {presigned_url}")
