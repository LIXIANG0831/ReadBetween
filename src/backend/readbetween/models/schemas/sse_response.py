import json
from typing import Any, Dict, Optional
from enum import Enum


class StreamEventType(Enum):
    """流式事件类型枚举"""
    START = "START"  # 开始事件
    MESSAGE = "MESSAGE"  # 消息内容
    TOOL_START = "TOOL_START"  # 工具调用开始
    TOOL_END = "TOOL_END"  # 工具调用结束
    TOOL_FINISH = "TOOL_FINISH"  # 工具调用完成
    SOURCE = "SOURCE"  # 来源信息
    ERROR = "ERROR"  # 错误信息
    END = "END"  # 结束事件


class StreamResponseTemplate:
    """流式响应模板类"""

    @staticmethod
    def format_response(
            event: Enum,
            text: str = "",
            extra: Optional[Any] = None
    ) -> str:
        """
        格式化流式响应

        Args:
            event: 事件类型枚举
            text: 文本内容
            extra: 额外数据

        Returns:
            SSE格式的字符串
        """
        data = {
            "event": event.value,
            "text": text
        }

        if extra is not None:
            data["extra"] = extra

        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    @staticmethod
    def start_event() -> str:
        """开始事件"""
        return StreamResponseTemplate.format_response(StreamEventType.START)

    @staticmethod
    def message_event(text: str) -> str:
        """消息事件"""
        return StreamResponseTemplate.format_response(StreamEventType.MESSAGE, text)

    @staticmethod
    def tool_start_event(tool_calls: list) -> str:
        """工具调用开始事件"""
        return StreamResponseTemplate.format_response(
            StreamEventType.TOOL_START,
            extra=tool_calls
        )

    @staticmethod
    def tool_end_event(tool_response: dict) -> str:
        """工具调用结束事件"""
        return StreamResponseTemplate.format_response(
            StreamEventType.TOOL_END,
            extra=tool_response
        )

    @staticmethod
    def tool_finish_event(tool_result: dict) -> str:
        """工具调用完成事件"""
        return StreamResponseTemplate.format_response(
            StreamEventType.TOOL_FINISH,
            extra=tool_result
        )

    @staticmethod
    def source_event(sources: list) -> str:
        """来源信息事件"""
        return StreamResponseTemplate.format_response(
            StreamEventType.SOURCE,
            extra=sources
        )

    @staticmethod
    def error_event(error_message: str) -> str:
        """错误事件"""
        return StreamResponseTemplate.format_response(
            StreamEventType.ERROR,
            error_message
        )

    @staticmethod
    def end_event() -> str:
        """结束事件"""
        return StreamResponseTemplate.format_response(StreamEventType.END)
