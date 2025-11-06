from sqlmodel import SQLModel


class AwsomeDBModel(SQLModel):
    # 确保模型被注册到 metadata
    class Config:
        arbitrary_types_allowed = True
