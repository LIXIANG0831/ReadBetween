import asyncio
from typing import Dict
from fastapi import HTTPException
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
from livekit.agents.cli.cli import proto
from livekit.agents.cli.log import setup_logging
from livekit.agents.worker import Worker
from livekit.protocol import models

from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero, deepgram, cartesia
from readbetween.utils.logger_util import logger_util
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.settings import get_config

deepgram_api_key = get_config("api.deepgram.api_key")
cartesia_api_key = get_config("api.cartesia.api_key")
llm_base_url = get_config("api.openai.base_url")
llm_api_key = get_config("api.openai.api_key")
livekit_url = get_config("api.livekit.livekit_url")
livekit_api_secret = get_config("api.livekit.livekit_api_secret")
livekit_api_key = get_config("api.livekit.livekit_api_key")

"""
Deprecated 
"""
class VoiceAgentService:
    def __init__(self, worker_type=WorkerType.ROOM, agent_name: str = None, prompt: str = None, welcome_words: str = None, participant_identity: str = None):
        self.worker_type = worker_type
        self.agent = None
        self.usage_collector = None
        self.chat = None
        self.agent_name = agent_name
        self.prompt = prompt
        self.welcome_words = welcome_words
        self.participant_identity = participant_identity

    def _prewarm(self, proc: JobProcess):
        try:
            proc.userdata["vad"] = silero.VAD.load()
        except Exception as e:
            logger_util.error(f"预热失败: {e}", exc_info=True)

    async def _request_fnc(self, req: JobRequest):
        try:
            agent_name = self.agent_name or "LIXIANG's 个人助理"
            await req.accept(name=agent_name, identity=f"{req.id}")
        except Exception as e:
            logger_util.error(f"请求处理失败: {e}", exc_info=True)

    async def _entrypoint(self, ctx: JobContext):
        try:
            must_contain_prompt = (
                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
                "You need to reply in Chinese."
            )
            system_prompt = (
                self.prompt or "You are a voice assistant created by 李响. Your interface with users will be voice. "
            ) + must_contain_prompt

            initial_ctx = llm.ChatContext().append(role="system", text=system_prompt)

            logger_util.info(f"connecting to room {ctx.room.name}")
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

            if self.participant_identity is None:
                # 监听首个参会者
                participant = await ctx.wait_for_participant()
            else:
                # 等待特定参会者
                participant = await ctx.wait_for_participant(identity=self.participant_identity)

            logger_util.info(
                f"starting voice assistant for participant : {participant.name=} | {participant.identity=}")

            self.agent = VoicePipelineAgent(
                vad=ctx.proc.userdata["vad"],
                stt=deepgram.STT(api_key=deepgram_api_key, language="zh-CN"),
                llm=openai.LLM(base_url=llm_base_url, api_key=llm_api_key, model="COSMO-GPT"),
                tts=cartesia.TTS(api_key=cartesia_api_key, language="zh"),
                chat_ctx=initial_ctx,
            )

            self.agent.start(ctx.room, participant)

            # self.usage_collector = metrics.UsageCollector()

            # @self.agent.on("metrics_collected")
            # def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
            #     metrics.log_metrics(mtrcs)
            #     self.usage_collector.collect(mtrcs)

            # async def log_usage():
            #     summary = self.usage_collector.get_summary()
            #     logger_util.info(f"Usage: ${summary}")
            #
            # ctx.add_shutdown_callback(log_usage)

            self.chat = rtc.ChatManager(ctx.room)

            async def answer_from_text(txt: str):
                logger_util.info(f"接收到用户输入: {txt=}")
                chat_ctx = self.agent.chat_ctx.copy()
                chat_ctx.append(role="user", text=txt)
                stream = self.agent.llm.chat(chat_ctx=chat_ctx)
                logger_util.info(f"LLM处理并输出: {stream=}")
                await self.agent.say(stream)

            @self.chat.on("message_received")
            def on_chat_received(msg: rtc.ChatMessage):
                if msg.message:
                    asyncio.create_task(answer_from_text(msg.message))

            if self.welcome_words is None:
                self.welcome_words = "你好, 今天过的怎么样?"
            await self.agent.say(self.welcome_words, allow_interruptions=True)
        except Exception as e:
            logger_util.error(f"入口点执行失败: {e}", exc_info=True)

    async def _run_worker(self, args: proto.CliArgs) -> None:

        setup_logging(args.log_level, args.devmode)
        args.opts.validate_config(args.devmode)

        loop = asyncio.get_event_loop()
        worker = Worker(args.opts, devmode=args.devmode, loop=loop)
        loop.set_debug(args.asyncio_debug)
        loop.slow_callback_duration = 0.1  # 100ms
        from livekit.agents import utils
        utils.aio.debug.hook_slow_callbacks(2)

        if args.room and args.reload_count == 0:
            # directly connect to a specific room
            @worker.once("worker_registered")
            def _connect_on_register(worker_id: str, server_info: models.ServerInfo):
                logger_util.info("connecting to room %s", args.room)
                loop.create_task(worker.simulate_job(args.room, args.participant_identity))

        watch_client = None
        if args.watch:
            from livekit.agents.cli.watcher import WatchClient
            watch_client = WatchClient(worker, args, loop=loop)
            watch_client.start()

        try:
            await worker.run()
        except Exception:
            logger_util.exception("worker failed")
        finally:
            if watch_client:
                await watch_client.aclose()
            await worker.aclose()

    async def run_voice_agent(self):
        try:
            logger_util.info("开始运行实时语音服务")
            # cli.run_app(
            #     WorkerOptions(
            #         ws_url=livekit_url,
            #         api_key=livekit_api_key,
            #         api_secret=livekit_api_secret,
            #         entrypoint_fnc=self.entrypoint,
            #         prewarm_fnc=self.prewarm,
            #         request_fnc=self.request_fnc,
            #         worker_type=self.worker_type,  # 每个房间一个新的Agent示例
            #     ),
            # )
            opts = WorkerOptions(
                ws_url=livekit_url,
                api_key=livekit_api_key,
                api_secret=livekit_api_secret,
                entrypoint_fnc=self._entrypoint,
                prewarm_fnc=self._prewarm,
                request_fnc=self._request_fnc,
                worker_type=self.worker_type,  # 每个房间一个新的Agent示例
            )
            args = proto.CliArgs(
                opts=opts,
                log_level="INFO",
                devmode=False,
                asyncio_debug=False,
                watch=False,
                drain_timeout=60,
            )
            await self._run_worker(args)

        except Exception as e:
            import logging
            logging.info(f"开启实时语音服务{self.agent_name}失败: {e}", exc_info=True, stack_info=True)
            # logger_util.error(f"开启实时语音服务{self.agent_name}失败: {e}", exc_info=True)