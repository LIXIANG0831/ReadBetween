<template>
  <div>
    <h1>实时语音交互</h1>

    <p>状态: {{ status }}</p>

    <button @click="startRecording" :disabled="isRecording">开始录音</button>
    <button @click="stopRecording" :disabled="!isRecording">停止录音</button>

    <div v-if="isRecording">
      <p>正在录音... 请说话</p>
    </div>

    <div>
      <h3>用户输入:</h3>
      <p>{{ userInput }}</p>
    </div>

    <div>
      <h3>AI 助手回复:</h3>
      <p>{{ assistantResponse }}</p>
    </div>
  </div>
</template>

<script>
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

export default {
  name: 'VoiceInteraction',
  data() {
    return {
      status: '准备就绪',
      isRecording: false,
      userInput: '',
      assistantResponse: '',
      deepgram: null,
      deepgramLive: null,
      llmApiKey: 'AIzaSyCrOkzFQMddu2oP3EgYbBwbqcGbQwlwhC8', // 替换为你的 LLM API 密钥 -  **重要安全提示: 生产环境请勿硬编码 API 密钥!**
      deepgramApiKey: '4d9e3cd47e8fcb14da95efb8a33ed56329ec61c9', // 替换为你的 Deepgram API 密钥 - **重要安全提示: 生产环境请勿硬编码 API 密钥!**
      microphoneStream: null,
    };
  },
  mounted() {
    this.initDeepgram();
  },
  beforeUnmount() {
    this.stopDeepgramLive();
  },
  methods: {
    initDeepgram() {
      console.log('initDeepgram 函数被调用');
      if (!this.deepgramApiKey) {
        this.status = '请设置 Deepgram API 密钥';
        return;
      }
      try {
        this.deepgram = createClient({
          key: this.deepgramApiKey,
        });
        this.status = 'Deepgram 初始化完成';
        console.log('Deepgram 初始化成功', this.deepgram);
      } catch (error) {
        this.status = 'Deepgram 初始化失败: ' + error;
        console.error('Deepgram 初始化失败:', error);
      }
    },
    async startRecording() {
      console.log('startRecording 函数被调用了');
      if (!this.deepgram) {
        this.status = 'Deepgram 未初始化';
        return;
      }

      this.userInput = '';
      this.assistantResponse = '';
      this.isRecording = true;
      this.status = '正在连接 Deepgram...';

      try {
        const connection = this.deepgram.listen.live({
          model: "nova-2",
          language: "zh-CN",
          smart_format: true,
          punctuate: true,
        });

        this.deepgramLive = connection;

        connection.on(LiveTranscriptionEvents.Open, () => {
          this.status = 'Deepgram 连接已打开，开始录音';
          console.log('Deepgram Open event triggered');
          this.startMicrophoneStream(connection);
        });

        connection.on(LiveTranscriptionEvents.Transcript, async (data) => {
          if (data.channel.alternatives[0]) {
            const text = data.channel.alternatives[0].transcript.trim();
            if (text) {
              this.userInput = text;
              this.status = '用户输入已转录: ' + text;
              await this.sendToLLM(text);
            }
          }
        });

        connection.on(LiveTranscriptionEvents.Error, (error) => {
          this.status = 'Deepgram 错误: ' + error;
          console.error('Deepgram Error event', error);
          this.stopRecording();
        });

        connection.on(LiveTranscriptionEvents.Close, () => {
          this.status = 'Deepgram 连接已关闭';
          console.log('Deepgram Close event triggered');
          this.isRecording = false;
          this.stopMicrophoneStream();
        });

      } catch (error) {
        this.status = '连接 Deepgram 失败: ' + error;
        console.error('连接 Deepgram 失败:', error);
        this.isRecording = false;
      }
    },
    stopRecording() {
      if (this.deepgramLive) {
        this.status = '正在关闭 Deepgram 连接...';
        this.deepgramLive.close();
        this.deepgramLive = null;
      }
      this.isRecording = false;
    },
    startMicrophoneStream(connection) { // 接收 connection 对象
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
          this.microphoneStream = stream;
          console.log('getUserMedia success', stream);
          const audioContext = new AudioContext();
          console.log('AudioContext 状态 (创建后):', audioContext.state);
          if (audioContext.state !== 'running') {
            audioContext.resume().then(() => {
              console.log('AudioContext 已 resume, 状态:', audioContext.state);
            }).catch(error => {
              console.error('AudioContext resume 失败:', error);
            });
          }

          const microphoneSource = audioContext.createMediaStreamSource(stream);
          console.log('MediaStreamSource created');
          const processor = audioContext.createScriptProcessor(4096, 1, 1);
          console.log('ScriptProcessor created');

          microphoneSource.connect(processor);
          console.log('MediaStreamSource connected to processor');
          processor.connect(audioContext.destination);
          console.log('Processor connected to audioContext.destination');

          processor.onaudioprocess = (event) => {
            // console.log('onaudioprocess triggered');
            // console.log('onaudioprocess 时 AudioContext 状态:', audioContext.state);
            const audioData = event.inputBuffer.getChannelData(0);
            const buffer = this.audioBufferToUint8Array(audioData);
            
            
            connection.send(buffer.buffer);
            
          };
          console.log('onaudioprocess 事件监听器已添加');

        })
        .catch((error) => {
          this.status = '麦克风访问失败: ' + error;
          console.error('getUserMedia error', error);
          this.isRecording = false;
        });
    },
    stopMicrophoneStream() {
      if (this.microphoneStream) {
        this.microphoneStream.getTracks().forEach(track => track.stop());
        this.microphoneStream = null;
      }
    },
    stopDeepgramLive() {
      if (this.deepgramLive) {
        this.deepgramLive.close();
        this.deepgramLive = null;
      }
    },
    audioBufferToUint8Array(audioBuffer) {
      let uint8Array = new Uint8Array(audioBuffer.length * 2);
      let offset = 0;
      for (let i = 0; i < audioBuffer.length; i++) {
        let sample = audioBuffer[i];
        if (sample > 1) sample = 1; else if (sample < -1) sample = -1;
        sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        uint8Array[offset++] = sample & 0xFF;
        uint8Array[offset++] = (sample >>> 8) & 0xFF;
      }
      return uint8Array;
    },
    async sendToLLM(text) {
      this.status = '正在请求 AI 助手...';
      try {
        const response = await fetch('https://xianglee-gemini-play.deno.dev/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.llmApiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gemini-2.0-flash-exp',
            messages: [
              { role: 'system', content: 'You are a test assistant.' },
              { role: 'user', content: text },
            ],
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        this.assistantResponse = data.choices[0].message.content;
        this.status = 'AI 助手回复已收到';

      } catch (error) {
        this.status = '请求 AI 助手失败: ' + error;
        console.error('请求 AI 助手失败:', error);
        this.assistantResponse = '请求 AI 助手失败，请查看控制台错误信息。';
      }
    },
  },
};
</script>

<style scoped>
/* 组件样式 (可以根据需要自定义) */
button {
  margin: 10px;
  padding: 10px 20px;
  font-size: 16px;
}
</style>