<template>
  <div class="common-layout">
    <a-layout style="height: 100vh;">
      <a-layout-sider width="400" class="aside" style="height: 100%;">
        <div style="padding: 16px;height: 100%;display: flex;flex-direction: column;">
          <a-button type="primary" @click="isCreateDialogVisible = true" style="width: 200px;margin-bottom: 16px;">
            新建会话
          </a-button>
          <a-menu
            v-model:selectedKeys="activeKey"
            mode="inline"
            :style="style"
            @click="handleConversationClick"
          >
            <a-menu-item v-for="item in items" :key="item.id" class="menu-item">
              <template #icon>
                <message-outlined />
              </template>
              <span>{{ item.title || `会话 ${item.id}` }}</span>
              <div class="action-icons">
                <edit-outlined class="action-icon" @click.stop="handleEdit(item)" />
                <delete-outlined class="action-icon" @click.stop="handleDelete(item.id)" />
              </div>
            </a-menu-item>
          </a-menu>
        </div>
      </a-layout-sider>
      <a-layout>
        <a-layout-content class="main">
          <div style="padding: 16px;">
            <div style="margin-bottom: 16px;">
              <a-button @click="handleClearHistory" :disabled="!activeKey[0]">
                清除历史记录
              </a-button>
            </div>
            <Chat
              :chats="chats"
              @message-send="handleMessageSend"
              :loading="isLoading"
              showClearContext
              :roleConfig="roleConfig"
              :message-key="msg => msg.timestamp.toString()"
            />
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>

    <!-- 新建会话弹窗 -->
    <a-modal
      v-model:open="isCreateDialogVisible"
      :title="isEditing ? '编辑会话' : '新建会话'"
      width="500px"
      @cancel="handleModalClose"
    >
      <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="会话标题" name="title">
          <a-input v-model:value="form.title" placeholder="请输入会话标题" />
        </a-form-item>
        <a-form-item label="模型" name="model" required>
          <a-input v-model:value="form.model" disabled />
        </a-form-item>
        <a-form-item label="系统提示" name="system_prompt">
          <a-textarea v-model:value="form.system_prompt" :rows="4" />
        </a-form-item>
        <a-form-item label="温度">
          <div class="slider-container">
            <a-slider
              v-model:value="form.temperature"
              :min="0.1"
              :max="2"
              :step="0.1"
              :tooltip-formatter="value => `${value.toFixed(1)}`"
              style="flex: 1;"
            />
            <div class="value-display">
              {{ form.temperature !== undefined ? form.temperature.toFixed(1) : '0.0' }}
            </div>
          </div>
        </a-form-item>
        <a-form-item label="知识库">
          <a-select
            v-model:value="form.knowledge_base_ids"
            mode="multiple"
            placeholder="请选择知识库"
          >
            <a-select-option
              v-for="knowledge in knowledgeList"
              :key="knowledge.id"
              :value="knowledge.id"
            >
              {{ knowledge.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="handleModalClose">取消</a-button>
        <a-button type="primary" @click="handleConversationSubmit">
          {{ isEditing ? '更新' : '创建' }}
        </a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { Chat } from '@kousum/semi-ui-vue';
import { ref, onMounted, computed, watch } from 'vue';
import {
  message,
  Modal as AModal,
  Form as AForm,
  Input as AInput,
  Select as ASelect,
  Slider as ASlider,
  Menu as AMenu
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  MessageOutlined
} from '@ant-design/icons-vue';
import { theme } from 'ant-design-vue';
import {
  createConversation,
  listConversations,
  deleteConversation,
  updateConversation,
  clearMessageHistory,
  getMessageHistory,
  sendMessage
} from '@/api/conversations';
import { listKnowledge } from '@/api/knowledge';
import { useDefaultModelStore } from '@/store/useDefaultModelStore';

interface ExtendedChatMessage {
  content: string;
  role: 'user' | 'assistant';
  status?: 'loading' | 'error';
  timestamp: number;
}

interface StreamMessage {
  event: 'START' | 'MESSAGE' | 'SOURCE' | 'END';
  text?: string;
  [key: string]: any;
}

const roleConfig = ref({
  user: {
    name: 'User',
    avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/docs-icon.png'
  },
  assistant: {
    name: 'Assistant',
    avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/other/logo.png'
  }
});

const defaultModelStore = useDefaultModelStore();
const { token } = theme.useToken();

// 状态管理
const activeKey = ref<string[]>([]);
const items = ref<Api.Conversation[]>([]);
const chats = ref<ExtendedChatMessage[]>([]);
const knowledgeList = ref<Api.Knowledge[]>([]);
const isLoading = ref(false);
const isCreateDialogVisible = ref(false);
const isEditing = ref(false);

// 表单数据
const form = ref<Api.CreateConversationParams>({
  title: '新会话',
  model: '',
  system_prompt: '你是我的AI助手',
  temperature: 0.3,
  knowledge_base_ids: [],
});

// 样式计算
const style = computed(() => ({
  width: '100%',
  background: token.value.colorBgContainer,
  borderRadius: token.value.borderRadius,
  flex: 1,
}));

// 获取会话列表
const fetchConversations = async () => {
  try {
    const res = await listConversations();
    if (res.data.status_code === 200) {
      items.value = res.data.data.data;
      if (items.value.length > 0 && !activeKey.value.length) {
        activeKey.value = [items.value[0].id];
      }
    }
  } catch (error) {
    message.error('获取会话列表失败');
  }
};

// 获取消息历史
const fetchMessageHistory = async (convId: string) => {
  try {
    const res = await getMessageHistory({ conv_id: convId });
    if (res.data.status_code === 200) {
      chats.value = res.data.data.map(msg => ({
        content: msg.content,
        role: msg.role === 'user' ? 'user' : 'assistant',
        timestamp: new Date().getTime()
      }));
    }
  } catch (error) {
    message.error('获取消息历史失败');
  }
};

// 获取知识库列表
const fetchKnowledgeList = async () => {
  try {
    const res = await listKnowledge();
    if (res.data.status_code === 200) {
      knowledgeList.value = res.data.data.data;
    }
  } catch (error) {
    message.error('获取知识库失败');
  }
};

// 发送消息处理
const handleMessageSend = async (text: string) => {
  if (!activeKey.value[0] || !text.trim()) return;

  try {
    isLoading.value = true;

    // ================= 消息创建阶段 =================
    // 创建完全独立的消息对象
    const userMessage: ExtendedChatMessage = {
      content: text,  // 使用原始输入文本
      role: 'user',
      timestamp: Date.now()
    };

    const assistantMessage: ExtendedChatMessage = {
      content: '',
      role: 'assistant',
      status: 'loading',
      timestamp: userMessage.timestamp + 1  // 确保唯一性
    };

    // 不可变更新消息列表
    chats.value = [
      ...chats.value,
      userMessage,          // 用户消息固定不变
      assistantMessage      // 助手消息单独更新
    ];

    // ================= 流处理阶段 =================
    const response = await sendMessage({
      conv_id: activeKey.value[0],
      message: text,        // 使用原始输入文本
      temperature: form.value.temperature
    });

    if (!response.ok) throw new Error('Failed to get stream');

    const reader = response.body.getReader();
    let currentContent = '';
    let isStreamEnded = false;

    // 流处理核心逻辑
    const processStream = async () => {
      try {
        while (!isStreamEnded) {
          const { done, value } = await reader.read();
          if (done) {
            handleStreamEnd();
            return;
          }

          const chunkText = new TextDecoder().decode(value);
          const lines = chunkText.split('\n\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            
            try {
              const parsedData: StreamMessage = JSON.parse(line.slice(6));
              handleStreamEvent(parsedData);
            } catch (error) {
              console.error('JSON parse error:', error);
            }
          }
        }
      } catch (error) {
        handleStreamError(error);
      }
    };

    // ================= 事件处理器 =================
    const handleStreamEvent = (data: StreamMessage) => {
      switch (data.event) {
        case 'START':
          // 初始化处理
          break;
          
        case 'MESSAGE':
          currentContent += data.text || '';
          updateAssistantContent(currentContent);
          break;
          
        case 'SOURCE':
          console.log('Source data:', data);
          break;
          
        case 'END':
          handleStreamEnd();
          break;
      }
    };

    // ================= 关键更新方法 =================
    const updateAssistantContent = (content: string) => {
      // 严格匹配当前助手消息
      chats.value = chats.value.map(msg => {
        if (msg.timestamp === assistantMessage.timestamp) {
          return { 
            ...msg, 
            content, 
            status: content ? undefined : 'loading' 
          };
        }
        return msg;  // 保持用户和其他消息不变
      });
    };

    // ================= 结束处理 =================
    const handleStreamEnd = () => {
      isStreamEnded = true;
      isLoading.value = false;
      reader.cancel();
      
      // 最终状态更新
      chats.value = chats.value.map(msg => {
        if (msg.timestamp === assistantMessage.timestamp) {
          return { ...msg, status: undefined };
        }
        return msg;
      });
    };

    // ================= 错误处理 =================
    const handleStreamError = (error: any) => {
      console.error('Stream error:', error);
      isLoading.value = false;
      
      // 只修改当前助手消息状态
      chats.value = chats.value.map(msg => {
        if (msg.timestamp === assistantMessage.timestamp) {
          return { ...msg, status: 'error' };
        }
        return msg;  // 用户消息保持原样
      });
      
      message.error('消息处理失败');
    };

    await processStream();
  } catch (error) {
    console.error('Message send error:', error);
    isLoading.value = false;
    message.error('消息发送失败');
  } finally {
    // 确保清空输入框（需要Chat组件配合）
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  }
};


// 清除历史记录
const handleClearHistory = async () => {
  if (!activeKey.value[0]) return;

  try {
    await clearMessageHistory({ conv_id: activeKey.value[0] });
    chats.value = [];
    message.success('历史记录已清除');
  } catch (error) {
    message.error('清除历史记录失败');
  }
};

// 删除会话
const handleDelete = async (convId: string) => {
  try {
    await deleteConversation({ conv_id: convId });
    message.success('会话已删除');
    await fetchConversations();
    if (activeKey.value[0] === convId) {
      activeKey.value = [];
      chats.value = [];
    }
  } catch (error) {
    message.error('删除会话失败');
  }
};

// 编辑会话
const handleEdit = (item: Api.Conversation) => {
  isEditing.value = true;
  isCreateDialogVisible.value = true;
  form.value = {
    title: item.title,
    model: item.model,
    system_prompt: item.system_prompt,
    temperature: item.temperature,
    knowledge_base_ids: item.knowledge_base_ids,
    conv_id: item.id
  };
};

// 提交会话创建/更新
const handleConversationSubmit = async () => {
  try {
    if (isEditing.value) {
      await updateConversation(form.value as Api.UpdateConversationParams);
      message.success('会话更新成功');
    } else {
      await createConversation(form.value);
      message.success('会话创建成功');
    }
    await fetchConversations();
    handleModalClose();
  } catch (error) {
    message.error(isEditing.value ? '更新会话失败' : '创建会话失败');
  }
};

// 弹窗关闭处理
const handleModalClose = () => {
  isCreateDialogVisible.value = false;
  isEditing.value = false;
  form.value = {
    title: '新会话',
    model: defaultModelStore.defaultModelCfg?.llm_name || '',
    system_prompt: '你是我的AI助手',
    temperature: 0.3,
    knowledge_base_ids: []
  };
};

// 会话点击处理
const handleConversationClick = ({ key }: { key: string }) => {
  activeKey.value = [key];
  fetchMessageHistory(key);
};

// 初始化
onMounted(async () => {
  await fetchConversations();
  await fetchKnowledgeList();
  defaultModelStore.loadDefaultModelCfg();
  form.value.model = defaultModelStore.defaultModelCfg?.llm_name || '';
});

// 监听模型配置变化
watch(() => defaultModelStore.defaultModelCfg, (newVal) => {
  if (newVal) {
    form.value.model = newVal.llm_name;
  }
}, { immediate: true });
</script>

<style scoped>
/* 保持原有样式不变 */
.common-layout {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.aside {
  background-color: v-bind('token.colorBgContainer');
  overflow: auto;
  height: 100%;
}

.slider-container {
  display: flex;
  align-items: center;
  width: 100%;
}

.value-display {
  width: 50px;
  text-align: center;
  padding: 0 8px;
  background: v-bind('token.colorFillAlter');
  border-radius: 4px;
  margin-left: 12px;
}

.main {
  background-color: v-bind('token.colorBgElevated');
  padding: 16px;
  flex: 1;
  overflow: auto;
  height: 100%;
}

.menu-item {
  position: relative;
}

.action-icons {
  display: none;
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.menu-item:hover .action-icons {
  display: flex;
}

.action-icon {
  margin-left: 8px;
  cursor: pointer;
}

.a-layout, .a-layout-sider, .a-layout-content {
  height: 100%;
}
</style>