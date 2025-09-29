from functools import lru_cache
from typing import Literal, Tuple

import click
import librosa
import numpy as np
from faster_whisper import WhisperModel
from fastrtc import audio_to_float32
from fastrtc.speech_to_text.stt_ import STTModel
from numpy.typing import NDArray


class FasterWhisperModel(STTModel):
    def __init__(
            self,
            model_size: Literal["tiny", "base", "small", "medium", "large"] = "base",
            compute_type: Literal["float32", "int8", "int8_float16", "float16"] = "float32",
            language: str = "zh",
            device: Literal["cpu", "cuda"] = "auto"
    ):
        """
        初始化Faster Whisper语音识别模型

        参数:
            model_size: 模型大小（tiny/base/small/medium/large）
            compute_type: 计算精度类型
            language: 默认识别语言代码
            device: 运行设备（cpu/cuda）
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "Please install faster-whisper with: pip install faster-whisper"
            )

        self.model = WhisperModel(
            model_size_or_path=model_size,
            compute_type=compute_type,
            device=device
        )
        self.language = language

    def stt(self, audio: Tuple[int, NDArray[np.int16 | np.float32]]) -> str:
        """
        执行语音转文字识别

        参数:
            audio: (采样率, 音频数据)元组

        返回:
            识别出的文本内容
        """
        sr, audio_np = audio
        audio_np = audio_to_float32(audio_np)  # 统一转为float32

        # 重采样到16kHz（Whisper标准输入）
        if sr != 16000:
            audio_np = librosa.resample(
                audio_np,
                orig_sr=sr,
                target_sr=16000
            )
        if audio_np.ndim == 1:
            audio_np = audio_np.reshape(1, -1)

        # 执行识别
        segments, _ = self.model.transcribe(
            audio_np.reshape(-1),
            language=self.language
        )

        return " ".join(segment.text for segment in segments).strip()


@lru_cache(maxsize=2)
def get_faster_whisper_stt_model(
        model_size: Literal["tiny", "base", "small", "medium", "large"] = "base",
        compute_type: Literal["float32", "int8", "int8_float16", "float16"] = "float32",
        language: str = "zh",
        device: Literal["cpu", "cuda"] = "auto"
) -> STTModel:
    """
    获取带缓存的Faster Whisper模型实例

    参数同FasterWhisperModel初始化参数
    """
    stt_model = FasterWhisperModel(
        model_size=model_size,
        compute_type=compute_type,
        language=language,
        device=device
    )

    # 预热模型
    print(click.style("INFO", fg="green") + ":\t 预热 Faster Whisper model...")
    dummy_audio = np.random.rand(16000).astype(np.float32)  # 1秒空白音频
    stt_model.stt((16000, dummy_audio))
    print(click.style("INFO", fg="green") + ":\t Faster Whisper model 就绪.")

    return stt_model


def test_faster_whisper() -> None:
    model = WhisperModel("base", compute_type="float32")

    # segments, info = model.transcribe("audio1.mp3")
    segments, info = model.transcribe("audio1.mp3", language="zh")
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))


if __name__ == '__main__':
    # test_faster_whisper()
    audio_path = "audio.mp3"
    audio_np, sr = librosa.load(audio_path, sr=None)

    # stt_model = get_stt_model()
    stt_model = get_faster_whisper_stt_model()

    print((sr, audio_np))

    text = stt_model.stt((sr, audio_np))
    print(text)
