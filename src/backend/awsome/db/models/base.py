from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, DateTime, text


class AwsomeDBModel(SQLModel):
    # 删除标识
    delete: int = Field(index=False, default=0)
    # 创建时间
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            index=True,
            server_default=text('CURRENT_TIMESTAMP')
        )
    )
    # 修改时间
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        )
    )
