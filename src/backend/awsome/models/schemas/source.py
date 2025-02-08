from pydantic import BaseModel


class SourceMsg(BaseModel):
    def __init__(self, source, title, url):
        """
        用于表示召回结果的通用类。
        :param source: 来源（"es" 或 "milvus"）
        :param title: 标题
        :param url: 来源url
        """
        self.source = source  # 数据来源（"kb" 或 "web"）
        self.title = title  # 标题
        self.url = url  # 来源url

    def to_dict(self):
        """
        将来源信息转换为字典格式，方便后续处理。
        """
        result_dict = {
            "source": self.source,
            "title": self.title,
            "url": self.url,
        }
        return result_dict