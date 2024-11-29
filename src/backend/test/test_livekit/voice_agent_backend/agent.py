import logging

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import cartesia, deepgram, openai, silero

# 加载环境变量
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")  # 创建一个日志记录器

# 预热函数，用于加载 VAD（语音活动检测）模型
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()  # 加载 Silero 的 VAD 模型

# 入口点函数，处理与用户的交互
async def entrypoint(ctx: JobContext):
    # 初始化聊天上下文，设置助手的系统角色和行为
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")  # 记录连接房间的信息
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)  # 连接房间，只订阅音频

    # 等待第一个参与者连接
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")  # 记录参与者信息

    # 配置语音助手，使用 Deepgram 进行语音识别，OpenAI 作为语言模型，Cartesia 进行文本转语音
    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],  # 使用预热时加载的 VAD
        stt=deepgram.STT(language='zh-CN'),  # 设置语音识别为中文
        llm=openai.LLM(model="ycpc-gpt"),  # 设置语言模型
        tts=cartesia.TTS(language='zh-CN'),  # 设置文本转语音为中文
        chat_ctx=initial_ctx,  # 设置聊天上下文
    )

    assistant.start(ctx.room, participant)  # 启动语音助手

    # 语音助手应礼貌地问候用户
    await assistant.say("你好！今天过的怎么样呀。", allow_interruptions=True)  # 向用户问好

# 主程序入口
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,  # 设置入口点函数
            prewarm_fnc=prewarm,  # 设置预热函数
        ),
    )
