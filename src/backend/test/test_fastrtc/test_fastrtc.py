# pip install "fastrtc[vad, stt, tts]"
from fastrtc import (ReplyOnPause, Stream, get_tts_model)
from openai import OpenAI

from test.test_fastrtc.test_stt_faster_whisper import get_faster_whisper_stt_model
from test.test_fastrtc.test_tts_kokoro import get_kokoro_v11_tts_model

llm_client = OpenAI(
    api_key="sk-", base_url="https://abc.ycpc.com/v1"
)

tts_model = get_kokoro_v11_tts_model()
stt_model = get_faster_whisper_stt_model()


def echo(audio):

    prompt = stt_model.stt(audio)
    print(f"接收到语音输入: {prompt=}")

    response = llm_client.chat.completions.create(
        model="ycpc-gpt",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    prompt = response.choices[0].message.content

    print(f"LLM回复内容: {prompt=}")

    for audio_chunk in tts_model.stream_tts_sync(prompt):
        yield audio_chunk


stream = Stream(ReplyOnPause(echo), modality="audio", mode="send-receive")

stream.ui.launch(share=True, server_port=8881)
