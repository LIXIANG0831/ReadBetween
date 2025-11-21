<template>
  <div class="voice-assistant">
    <div class="container">
      <!-- 连接状态 -->
      <div class="status" :class="connectionStatus">
        {{ statusMessages[connectionStatus] }}
      </div>

      <!-- 主界面 -->
      <div class="main-panel" v-if="connectionStatus === 'connected'">
        <!-- 语音状态指示器 -->
        <div class="voice-indicator">
          <div 
            class="mic-icon" 
            :class="{ 
              'listening': isListening, 
              'speaking': isSpeaking,
              'muted': isMuted
            }"
            @click="toggleMute"
          >
            <span v-if="isMuted">🎤❌</span>
            <span v-else-if="isListening">🎤🔴</span>
            <span v-else-if="isSpeaking">🎤🔊</span>
            <span v-else>🎤</span>
          </div>
          <div class="voice-status">
            {{ voiceStatusText }}
          </div>
        </div>

        <!-- 对话记录 -->
        <div class="chat-history">
          <div 
            v-for="(message, index) in messages" 
            :key="index" 
            :class="['message', message.type]"
          >
            <div class="message-content">
              {{ message.content }}
            </div>
            <div class="message-time">
              {{ message.timestamp }}
            </div>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="controls">
          <button 
            @click="toggleConnection" 
            class="btn btn-disconnect"
            :disabled="connecting"
          >
            {{ connecting ? '断开中...' : '断开连接' }}
          </button>
          <button 
            @click="clearMessages" 
            class="btn btn-clear"
          >
            清空记录
          </button>
        </div>
      </div>

      <!-- 连接界面 -->
      <div class="connect-panel" v-else>
        <h2>ReadBetween 语音助手</h2>
        <p>与晓晴进行语音对话</p>
        
        <div class="input-group">
          <label>LiveKit 服务器 URL:</label>
          <input 
            v-model="serverUrl" 
            type="text" 
            placeholder="ws://124.222.245.152:7880"
          />
        </div>

        <div class="input-group">
          <label>Token 后端地址:</label>
          <input 
            v-model="tokenBackendUrl" 
            type="text" 
            placeholder="http://localhost:8088"
          />
        </div>

        <div class="input-group">
          <label>房间名称:</label>
          <input 
            v-model="roomName" 
            type="text" 
            placeholder="assistant-room"
          />
        </div>

        <div class="input-group">
          <label>用户名称:</label>
          <input 
            v-model="userName" 
            type="text" 
            placeholder="你的名字"
          />
        </div>

        <button 
          @click="connectToRoom" 
          class="btn btn-connect"
          :disabled="connecting"
        >
          {{ connecting ? '连接中...' : '开始对话' }}
        </button>

        <!-- 错误信息显示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Room, RemoteParticipant, RemoteTrackPublication } from 'livekit-client';

export default {
  name: 'VoiceAssistant',
  data() {
    return {
      // 连接配置
      serverUrl: 'ws://124.222.245.152:7880',
      tokenBackendUrl: 'http://localhost:8080',
      roomName: 'assistant-room',
      userName: '用户',
      
      // 状态
      room: null,
      connectionStatus: 'disconnected',
      isListening: false,
      isSpeaking: false,
      isMuted: false,
      connecting: false,
      errorMessage: '',
      
      // 消息记录
      messages: [],
      
      // 状态消息映射
      statusMessages: {
        disconnected: '未连接',
        connecting: '连接中...',
        connected: '已连接',
        reconnecting: '重新连接中...'
      }
    };
  },
  
  computed: {
    voiceStatusText() {
      if (this.isMuted) return '麦克风已静音';
      if (this.isListening) return '正在聆听...';
      if (this.isSpeaking) return '晓晴正在说话...';
      return '准备就绪';
    }
  },
  
  methods: {
    // 从后端获取 token
    async getToken(userName, roomName) {
      try {
        console.log('正在获取 token...', { userName, roomName });
        
        const url = `${this.tokenBackendUrl}/sys/getVoiceToken?name=${encodeURIComponent(userName)}&room=${encodeURIComponent(roomName)}`;
        
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });
        
        console.log('Token 响应状态:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`获取 token 失败: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Token 响应数据:', data);
        
        if (data.code === 200 && data.data) {
          return data.data;
        } else if (data.token) {
          return data.token;
        } else {
          throw new Error('无效的 token 响应格式');
        }
        
      } catch (error) {
        console.error('获取 token 错误:', error);
        throw error;
      }
    },

    // 简化连接选项，避免 structuredClone 错误
    async connectToRoom() {
      if (this.connecting) return;
      
      this.connecting = true;
      this.errorMessage = '';
      this.connectionStatus = 'connecting';
      this.addMessage('system', '正在连接到语音助手...');
      
      try {
        // 验证输入
        if (!this.userName.trim()) {
          throw new Error('请输入用户名称');
        }
        if (!this.roomName.trim()) {
          throw new Error('请输入房间名称');
        }
        if (!this.serverUrl.trim()) {
          throw new Error('请输入 LiveKit 服务器 URL');
        }
        if (!this.tokenBackendUrl.trim()) {
          throw new Error('请输入 Token 后端地址');
        }

        // 获取访问令牌
        const token = await this.getToken(this.userName, this.roomName);
        console.log('获取到的 token:', token);
        
        if (!token) {
          throw new Error('获取到的 token 为空');
        }

        // 创建房间实例 - 使用更简单的配置
        this.room = new Room({
          adaptiveStream: false, // 禁用自适应流
          dynacast: false,       // 禁用 dynacast
        });
        
        // 设置事件监听器
        this.setupRoomListeners();
        
        // 使用简化的连接选项
        console.log('正在连接到 LiveKit...', this.serverUrl);
        await this.room.connect(this.serverUrl, token, {
          autoSubscribe: true,
          // 不传递任何可能包含不可克隆对象的选项
        });
        
        console.log('LiveKit 连接成功');
        
        // 单独启用麦克风，而不是在连接选项中
        try {
          await this.room.localParticipant.setMicrophoneEnabled(true);
          console.log('麦克风启用成功');
        } catch (micError) {
          console.warn('麦克风启用失败:', micError);
          this.addMessage('error', '麦克风权限获取失败，请检查浏览器设置');
        }
        
        await this.room.localParticipant.setCameraEnabled(false);
        
        this.connectionStatus = 'connected';
        this.addMessage('system', '已连接到语音助手，晓晴正在为您服务...');
        
      } catch (error) {
        console.error('连接失败:', error);
        this.connectionStatus = 'disconnected';
        this.errorMessage = error.message;
        this.addMessage('error', `连接失败: ${error.message}`);
      } finally {
        this.connecting = false;
      }
    },

    // 替代方案：使用更基础的连接方法
    async connectToRoomAlternative() {
      if (this.connecting) return;
      
      this.connecting = true;
      this.errorMessage = '';
      this.connectionStatus = 'connecting';
      
      try {
        // 获取访问令牌
        const token = await this.getToken(this.userName, this.roomName);
        
        // 使用更基础的 Room 配置
        this.room = new Room();
        
        // 设置基本的事件监听
        this.room.on('connected', () => {
          console.log('Room connected');
          this.connectionStatus = 'connected';
          this.addMessage('system', '连接成功');
        });
        
        this.room.on('disconnected', () => {
          console.log('Room disconnected');
          this.connectionStatus = 'disconnected';
        });
        
        // 连接房间
        await this.room.connect(this.serverUrl, token);
        
        // 手动启用音频
        if (this.room.localParticipant) {
          await this.room.localParticipant.setMicrophoneEnabled(true);
        }
        
      } catch (error) {
        console.error('连接失败:', error);
        this.connectionStatus = 'disconnected';
        this.errorMessage = error.message;
        this.addMessage('error', `连接失败: ${error.message}`);
      } finally {
        this.connecting = false;
      }
    },
    
    // 设置房间事件监听器
    setupRoomListeners() {
      if (!this.room) return;
      
      // 连接状态变化
      this.room.on('connectionStateChanged', (state) => {
        console.log('连接状态:', state);
        this.connectionStatus = state.toLowerCase();
        
        if (state === 'connected') {
          this.addMessage('system', '连接已建立');
        } else if (state === 'disconnected') {
          this.addMessage('system', '连接已断开');
        } else if (state === 'reconnecting') {
          this.addMessage('system', '正在重新连接...');
        }
      });
      
      // 参与者连接
      this.room.on('participantConnected', (participant) => {
        console.log('参与者加入:', participant.identity);
        this.setupParticipantListeners(participant);
        this.addMessage('system', `${participant.identity} 加入了房间`);
      });
      
      // 参与者断开连接
      this.room.on('participantDisconnected', (participant) => {
        console.log('参与者离开:', participant.identity);
        this.addMessage('system', `${participant.identity} 离开了房间`);
      });
      
      // 远程轨道订阅
      this.room.on('trackSubscribed', (track, publication, participant) => {
        console.log('远程轨道订阅:', track.kind, participant.identity);
        
        if (track.kind === 'audio') {
          try {
            const audioElement = new Audio();
            audioElement.srcObject = new MediaStream([track.mediaStreamTrack]);
            audioElement.play().catch(error => {
              console.log('音频播放失败:', error);
            });
          } catch (audioError) {
            console.log('创建音频元素失败:', audioError);
          }
        }
      });
      
      // 说话状态变化
      this.room.localParticipant.on('isSpeakingChanged', (speaking) => {
        this.isListening = speaking;
      });
      
      // 设置现有参与者的监听器
      this.room.remoteParticipants.forEach(participant => {
        this.setupParticipantListeners(participant);
      });
    },
    
    // 设置参与者事件监听器
    setupParticipantListeners(participant) {
      // 监听说话状态
      participant.on('isSpeakingChanged', (speaking) => {
        if (participant.identity === 'ReadBetween语音助手' || participant.identity.includes('助手')) {
          this.isSpeaking = speaking;
          if (speaking) {
            console.log('助手开始说话');
            this.addMessage('system', '晓晴正在说话...');
          }
        }
      });
    },
    
    // 断开连接
    async toggleConnection() {
      if (this.room) {
        try {
          await this.room.disconnect();
        } catch (error) {
          console.log('断开连接时出错:', error);
        }
        this.room = null;
        this.connectionStatus = 'disconnected';
        this.isListening = false;
        this.isSpeaking = false;
        this.addMessage('system', '已断开连接');
      }
    },
    
    // 切换静音
    async toggleMute() {
      if (!this.room) return;
      
      try {
        this.isMuted = !this.isMuted;
        await this.room.localParticipant.setMicrophoneEnabled(!this.isMuted);
        
        if (this.isMuted) {
          this.addMessage('system', '麦克风已静音');
        } else {
          this.addMessage('system', '麦克风已开启');
        }
      } catch (error) {
        console.error('切换静音失败:', error);
        this.addMessage('error', '麦克风控制失败');
      }
    },
    
    // 添加消息到记录
    addMessage(type, content) {
      const timestamp = new Date().toLocaleTimeString();
      this.messages.push({
        type,
        content,
        timestamp
      });
      
      if (this.messages.length > 50) {
        this.messages = this.messages.slice(-30);
      }
      
      this.$nextTick(() => {
        const chatHistory = this.$el.querySelector('.chat-history');
        if (chatHistory) {
          chatHistory.scrollTop = chatHistory.scrollHeight;
        }
      });
    },
    
    // 清空消息记录
    clearMessages() {
      this.messages = [];
      this.addMessage('system', '对话记录已清空');
    }
  },
  
  beforeUnmount() {
    if (this.room) {
      this.room.disconnect();
    }
  }
};
</script>

<style scoped>
.voice-assistant {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif;
}

.container {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.status {
  padding: 8px 12px;
  border-radius: 20px;
  text-align: center;
  margin-bottom: 20px;
  font-weight: bold;
}

.status.disconnected {
  background: #ffebee;
  color: #c62828;
}

.status.connecting {
  background: #fff3e0;
  color: #ef6c00;
}

.status.connected {
  background: #e8f5e8;
  color: #2e7d32;
}

.status.reconnecting {
  background: #fff3e0;
  color: #ef6c00;
}

.main-panel {
  text-align: center;
}

.voice-indicator {
  margin: 20px 0;
}

.mic-icon {
  font-size: 48px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 10px;
}

.mic-icon.listening {
  animation: pulse 1s infinite;
  color: #f44336;
}

.mic-icon.speaking {
  color: #4caf50;
  animation: glow 1s infinite;
}

.mic-icon.muted {
  color: #9e9e9e;
}

.voice-status {
  font-size: 14px;
  color: #666;
}

.chat-history {
  height: 200px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px;
  margin: 20px 0;
  background: white;
  text-align: left;
}

.message {
  margin: 10px 0;
  padding: 8px;
  border-radius: 8px;
}

.message.user {
  background: #e3f2fd;
  margin-left: 20px;
}

.message.assistant {
  background: #f3e5f5;
  margin-right: 20px;
}

.message.system {
  background: #f5f5f5;
  font-style: italic;
  color: #666;
  text-align: center;
}

.message.error {
  background: #ffebee;
  color: #c62828;
}

.message-content {
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.controls {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-connect {
  background: #4caf50;
  color: white;
}

.btn-connect:hover:not(:disabled) {
  background: #45a049;
}

.btn-disconnect {
  background: #f44336;
  color: white;
}

.btn-disconnect:hover:not(:disabled) {
  background: #da190b;
}

.btn-clear {
  background: #ff9800;
  color: white;
}

.btn-clear:hover {
  background: #f57c00;
}

.connect-panel {
  text-align: center;
}

.connect-panel h2 {
  color: #333;
  margin-bottom: 10px;
}

.connect-panel p {
  color: #666;
  margin-bottom: 20px;
}

.input-group {
  margin: 15px 0;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 5px;
  color: #333;
  font-weight: bold;
}

.input-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 6px;
  margin-top: 15px;
  font-size: 14px;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

@keyframes glow {
  0% { text-shadow: 0 0 5px rgba(76, 175, 80, 0.5); }
  50% { text-shadow: 0 0 20px rgba(76, 175, 80, 0.8); }
  100% { text-shadow: 0 0 5px rgba(76, 175, 80, 0.5); }
}
</style>