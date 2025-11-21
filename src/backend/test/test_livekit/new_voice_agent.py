# pip install "livekit-agents[silero,turn-detector,deepgram,cartesia,openai]~=1.2"
# pip install "livekit-plugins-noise-cancellation~=0.2"
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero, openai, deepgram, cartesia
from livekit.plugins.turn_detector.multilingual import MultilingualModel


## LiveKit
# LIVEKIT_URL=<your LiveKit server URL>
# LIVEKIT_API_KEY=<your API Key>
# LIVEKIT_API_SECRET=<your API Secret>

## LLM
# OPENAI_BASE_URL= '<URL>'
# OPENAI_API_KEY= '<KEY>'

## TTS
# CARTESIA_API_KEY = '<KEY>'

## STT
# DEEPGRAM_API_KEY = '<KEY>'


class ReadBetweenAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a voice assistant created by 李响, and your name is 晓晴."
                "Your interface with users will be voice. "
                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
                "You need to reply in Chinese."
            ),
        )


server = AgentServer()


@server.rtc_session()
async def readbetween_voice_agent(ctx: agents.JobContext):
    room_name = ctx.room.name
    print(f"🎯 Agent 被分配到房间: {room_name}")

    # 添加连接状态监控
    def on_connection_state_change(state: rtc.ConnectionState):
        print(f"🔄 连接状态: {state}")
        if state == rtc.ConnectionState.CONN_CONNECTED:
            print("✅ 成功连接到 LiveKit 服务器")
        elif state == rtc.ConnectionState.CONN_DISCONNECTED:
            print("❌ 与 LiveKit 服务器断开连接")
        elif state == rtc.ConnectionState.CONN_RECONNECTING:
            print("🔄 正在重新连接到 LiveKit 服务器")

    ctx.room.on("connection_state_changed", on_connection_state_change)

    # 添加参与者加入监控
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"👤 参与者加入: {participant.identity}")

    ctx.room.on("participant_connected", on_participant_connected)

    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="zh-CN"),
        llm=openai.LLM(model="COSMO-Mind"),
        tts=cartesia.TTS(model="sonic-3", language="zh", voice="7a5d4663-88ae-47b7-808e-8f9b9ee4127b"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=ReadBetweenAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda
                    params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user, introduce yourself, and offer assistance."
    )


if __name__ == "__main__":
    import os

    if not os.getenv("LIVEKIT_URL") or "your LiveKit server" in os.getenv("LIVEKIT_URL", ""):
        print("⚠️  运行在本地模拟模式 - 未连接到实际 LiveKit 服务器")
    else:
        print("🔗 连接到 LiveKit 服务器:", os.getenv("LIVEKIT_URL"))
    agents.cli.run_app(server)
    # python new_voice_agent.py start ## 正常启动
    # python new_voice_agent.py console ## 终端交互启动
