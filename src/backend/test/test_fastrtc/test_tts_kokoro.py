import click
import torch
import numpy as np
from pathlib import Path
import soundfile as sf
from typing import AsyncGenerator, Generator
from numpy.typing import NDArray
from dataclasses import dataclass
from functools import lru_cache
from kokoro import KPipeline, KModel
import re
from fastrtc.text_to_speech.tts import TTSModel, TTSOptions


@dataclass
class KokoroTTSOptions(TTSOptions):
    """Kokoro TTS 选项配置"""
    voice: str = "zf_001"  # 默认音色
    speed: float = 1.0  # 语速
    lang: str = "zh"  # 默认语言
    speed_callable: callable = None  # 动态语速回调函数


class KokoroV11TTSModel(TTSModel[KokoroTTSOptions]):
    """Kokoro v1.1 TTS 模型实现"""

    def __init__(self, model: KModel, zh_pipeline: KPipeline):
        """初始化模型和管道"""
        self.model = model
        self.zh_pipeline = zh_pipeline
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def tts(
            self, text: str, options: KokoroTTSOptions | None = None
    ) -> tuple[int, NDArray[np.float32]]:
        """同步文本转语音"""
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent

        options = options or KokoroTTSOptions()

        # 加载音色张量
        voice_tensor = torch.load(f'{current_dir}/ckpts/kokoro-v1.1/voices/{options.voice}.pt', weights_only=True)

        # 计算语速（优先使用回调函数）
        speed = options.speed_callable(len(text)) if options.speed_callable else options.speed

        # 生成音频
        generator = self.zh_pipeline(text, voice=voice_tensor, speed=speed)
        result = next(generator)
        wav = result.audio

        # Convert tensor to numpy array before astype
        return 24000, wav.cpu().numpy().astype(np.float32)

    async def stream_tts(
            self, text: str, options: KokoroTTSOptions | None = None
    ) -> AsyncGenerator[tuple[int, NDArray[np.float32]], None]:
        """异步流式文本转语音"""
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent

        options = options or KokoroTTSOptions()

        # 加载音色张量
        voice_tensor = torch.load(f'{current_dir}/ckpts/kokoro-v1.1/voices/{options.voice}.pt', weights_only=True)

        # 计算语速
        speed = options.speed_callable(len(text)) if options.speed_callable else options.speed

        # 按标点分割句子
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        for s_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            # 为每个句子生成音频
            generator = self.zh_pipeline(sentence, voice=voice_tensor, speed=speed)
            result = next(generator)
            wav = result.audio

            # 在句子之间添加静音间隔
            if s_idx != 0:
                yield 24000, np.zeros(5000, dtype=np.float32)

            yield 24000, wav.cpu().numpy().astype(np.float32)

    def stream_tts_sync(
            self, text: str, options: KokoroTTSOptions | None = None
    ) -> Generator[tuple[int, NDArray[np.float32]], None, None]:
        """同步流式文本转语音"""
        import asyncio

        # 创建事件循环来运行异步生成器
        loop = asyncio.new_event_loop()
        iterator = self.stream_tts(text, options).__aiter__()

        while True:
            try:
                yield loop.run_until_complete(iterator.__anext__())
            except StopAsyncIteration:
                break


@lru_cache(maxsize=2)
def get_kokoro_v11_tts_model() -> TTSModel[KokoroTTSOptions]:
    """获取 Kokoro v1.1 TTS 模型（带缓存）"""
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent

    # 设备检测
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # 加载模型文件
    REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
    model_path = f'{current_dir}/ckpts/kokoro-v1.1/kokoro-v1_1-zh.pth'
    config_path = f'{current_dir}/ckpts/kokoro-v1.1/config.json'
    model = KModel(model=model_path, config=config_path, repo_id=REPO_ID).to(device).eval()

    # 英文处理管道（用于混合语言场景）
    en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)

    # 增强的英文发音回调
    def enhanced_en_callable(text):
        """英文单词发音增强"""
        pronunciation_map = {
            'ReadBetween': 'ɹˈiːdbɪtwˈiːn',
        }
        if text in pronunciation_map:
            return pronunciation_map[text]
        return next(en_pipeline(text)).phonemes

    # 中文处理管道（支持英文混合）
    zh_pipeline = KPipeline(lang_code='z', repo_id=REPO_ID, model=model, en_callable=enhanced_en_callable)

    # 创建TTS模型实例
    tts_model = KokoroV11TTSModel(model, zh_pipeline)

    # 预热模型
    print(click.style("INFO", fg="green") + ":\t 预热 KokoroV1.1 model...")
    tts_model.tts("预热 Kokoro model...")
    print(click.style("INFO", fg="green") + ":\t KokoroV1.1 model 就绪.")

    return tts_model


def main():
    """测试主函数"""
    tts = get_kokoro_v11_tts_model()

    # 定义动态语速回调函数
    def speed_callback(text_len):
        """根据文本长度动态调整语速"""
        if text_len <= 10:
            return 1.2  # 短文本快速朗读
        elif text_len <= 30:
            return 1.0  # 中等长度正常速度
        else:
            return 0.8  # 长文本慢速朗读

    # 测试选项配置
    options = KokoroTTSOptions(
        voice="zf_001",
        speed=1.0,
        speed_callable=speed_callback
    )

    # 测试文本（中英混合）
    test_texts = [
        "Hello, 世界!",
        "这是一个测试样例，展示Kokoro v1.1的TTS能力。",
        "Mixed language text with 中英文混杂。ReadBetween is pronounced correctly.",
        "长文本测试，这里是一段较长的文本内容，用于测试模型的流式处理能力和语速控制功能。" * 2
    ]

    # 输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # 测试普通TTS
    print("\n测试普通TTS合成...")
    for i, text in enumerate(test_texts[:2]):
        print(f"处理文本: {text}")
        sample_rate, audio = tts.tts(text, options)
        output_path = output_dir / f"test_{i}.wav"
        sf.write(str(output_path), audio, sample_rate)
        print(f"已保存到: {output_path}")

    # 测试流式TTS
    print("\n测试流式TTS合成...")
    for i, text in enumerate(test_texts[2:], start=2):
        print(f"流式处理文本: {text}")
        chunks = []
        for sr, chunk in tts.stream_tts_sync(text, options):
            chunks.append(chunk)

        combined = np.concatenate(chunks)
        output_path = output_dir / f"stream_test_{i}.wav"
        sf.write(str(output_path), combined, sr)
        print(f"已保存流式结果到: {output_path}")

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()
