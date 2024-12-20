import asyncio
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
    JobRequest,
    WorkerType,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero, deepgram, cartesia

load_dotenv()
logger = logging.getLogger("voice-assistant")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def request_fnc(req: JobRequest):
    # accept the job request
    await req.accept(
        # the agent's name (Participant.name), defaults to ""
        name="LIXIANG's 个人助理",
        # the agent's identity (Participant.identity), defaults to "agent-<jobid>"
        identity=f"{req.id}",
    )


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by 李响. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
            "You need to reply in Chinese."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant : {participant.name=} | {participant.identity=}")

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        # stt=openai.STT(),
        stt=deepgram.STT(language="zh-CN"),
        llm=openai.LLM(model="ycpc-gpt"),
        # llm=openai.LLM(),
        # tts=openai.TTS(),
        tts=cartesia.TTS(language="zh"),
        chat_ctx=initial_ctx,
    )

    agent.start(ctx.room, participant)

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)
        usage_collector.collect(mtrcs)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: ${summary}")

    ctx.add_shutdown_callback(log_usage)

    # listen to incoming chat messages, only required if you'd like the agent to
    # answer incoming messages from Chat
    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        # rag
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = agent.llm.chat(chat_ctx=chat_ctx)
        await agent.say(stream)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    await agent.say("你好, 今天过的怎么样?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            request_fnc=request_fnc,
            worker_type=WorkerType.ROOM,  # 每个房间一个新的Agent示例
        ),
    )
