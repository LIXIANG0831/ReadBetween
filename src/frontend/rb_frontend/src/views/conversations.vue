<template>
  <div class="common-layout">
    <a-layout style="height: 100vh;">
      <a-layout-sider width="250px" class="aside">
        <a-menu
          v-model:selectedKeys="activeKey"
          mode="inline"
          @click="handleConversationClick"
        >
          <t-button theme="primary" @click="isCreateDialogVisible = true" style="width: 200px;margin-bottom: 16px;">
            新建渠道
          </t-button>
          <a-menu-item v-for="item in conversation_items" :key="item.id" class="menu-item">
            <template #icon>
              <t-icon name="chat" />
            </template>
            <span>{{ item.title || `会话 ${item.id}` }}</span>
            <div class="action-icons">
              <EditOutlined class="action-icon" @click.stop="handleEdit(item)" />
              <DeleteOutlined class="action-icon" @click.stop="handleDelete(item.id)" />
            </div>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>
      <a-layout>
        <a-layout-content class="main">
          <div class="chat-box" v-if="activeKey.length > 0" style="width: 100%;">
            <t-chat
            ref="chatRef"
            style="height: 630px"
            :clear-history="showclearHistory"
            @clear="handleClearHistory"
            :reverse="false"
            :data="chatsList"
            :is-stream-load="isStreamLoading"
            :textLoading="isNewMsgLoading"
            @scroll="handleChatScroll"
            animation="moving"
            >

              <template #content="{ item, index }">
                
                <t-chat-reasoning v-if="item.reasoning?.length > 0" expand-icon-placement="right">
                  <template #header>
                    <t-chat-loading v-if="isStreamLoading && item.content.length === 0" text="思考中..." />
                    <div v-else style="display: flex; align-items: center">
                      <CheckCircleIcon style="color: var(--td-success-color-5); font-size: 20px; margin-right: 8px" />
                      <span>已深度思考</span>
                    </div>
                  </template>
                  <t-chat-content v-if="item.reasoning.length > 0" :content="item.reasoning" />
                </t-chat-reasoning>


                <!-- 工具调用卡片 -->
                <ToolCallCard 
                  v-if="item.role === 'tool' && item.tool_call_id" 
                  :tool-call="findToolCall(item.tool_call_id)"
                  :content="item.content"
                />
                <t-chat-content v-if="item.content && item.content.length > 0 && item.role != 'tool' " :content="item.content" />
                <!-- 新增图片展示 -->
                <div v-if="item.image_url" class="chat-image-container">
                  <img 
                    :src="item.image_url" 
                    class="chat-image" 
                    :style="{ maxWidth: imageWidth(item.image_url) }"
                    @load="onImageLoad"
                    loading="lazy"
                  />
                </div>
                <!-- 来源信息卡片 -->
                <SourceCard v-if="item.source && item.source.length > 0" :sources="item.source" />
              </template>
              
              <template #actions="{ item, index }">
                <t-chat-action
                  :content="item.content"
                  :operation-btn="['good', 'bad', 'replay', 'copy']"
                  @operation="handleOperation"
                />
              </template>
              <template #footer>
                <!-- 新增独立的图片预览区域，放在输入框上方 -->
                <div class="image-preview-container" v-if="uploadedImageFiles.length > 0">
                  <div 
                    v-for="(file, index) in uploadedImageFiles" 
                    :key="file.uid || index"
                    class="image-preview-item"
                    :class="{ 'is-uploading': file.status === 'progress' }"
                  >
                    <img 
                      :src="getImagePreview(file)" 
                      alt="Preview" 
                      class="preview-image"
                    />
                    <div class="upload-indicator" v-if="file.status === 'progress'">
                      <t-spinner size="small" />
                      <span class="upload-text">上传中...</span>
                    </div>
                    <div class="remove-btn" @click="removeImage(index)">
                      <CloseIcon />
                    </div>
                  </div>
                </div>

                <t-chat-sender 
                v-model="query"
                :textarea-props="{
                  placeholder: '请输入消息...',
                }" 
                :stop-disabled="isStreamLoading" 
                @file-select="onFileSelect"
                @send="handleMessageSend(query)" 
                class="chat-sender"
                @stop="onStop"> 
                  <template #prefix>
                    <div class="model-select">
                      <t-button class="check-box" :class="{ 'is-active': isSearchEnabled }" variant="base" @click="toggleSearch">
                        <SystemSumIcon />
                        <span>联网搜索</span>
                      </t-button>
                    </div>
                  </template>


                  <!-- 自定义操作区域的内容，默认支持图片上传、附件上传和发送按钮 -->
                  <template #suffix="{ renderPresets }">
                    <!-- 添加图片上传功能 -->
                    <component :is="renderPresets([
                      { 
                        name: 'uploadImage',
                        uploadProps: imageUploadProps,
                        action: handleFileUpload
                      },
                      {
                        name: 'uploadAttachment',
                        uploadProps: attachmentUploadProps,
                        action: handleFileUpload
                      }
                    ])" />
                    <!-- 在这里可以进行自由的组合使用，或者新增预设 -->
                    <!-- 不需要附件操作的使用方式 -->
                    <!-- <component :is="renderPresets([])" /> -->
                    <!-- 只需要附件上传的使用方式-->
                    <!-- <component :is="renderPresets([{ name: 'uploadAttachment' }])" /> -->
                    <!-- 只需要图片上传的使用方式-->
                    <!-- <component :is="renderPresets([{ name: 'uploadImage' }])" /> -->
                    <!-- 任意配置顺序-->
                    <!-- <component :is="renderPresets([{ name: 'uploadAttachment' }, { name: 'uploadImage' }])" /> -->
                  </template>
                </t-chat-sender>
              </template>  
            </t-chat>
            <t-button v-show="isShowToBottom" variant="text" class="bottomBtn" @click="backBottom">
              <div class="to-bottom">
                <ArrowDownIcon />
              </div>
            </t-button>
          </div>
          <div v-else class="read-between-placeholder">
            ReadBetween
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>

    <!-- 新建会话弹窗 -->
    <a-modal
      class="modal-size-xl"
      v-model:open="isCreateDialogVisible"
      :title="isEditing ? '编辑渠道' : '新建渠道'"
      @cancel="handleModalClose"
    >
      <a-form :model="CreateConversationForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="渠道标题" name="title">
          <a-input v-model:value="CreateConversationForm.title" placeholder="请输入渠道标题" />
        </a-form-item>
        <a-form-item label="模型" name="model" required>
          <a-select
            v-model:value="CreateConversationForm.model"
            placeholder="请选择模型"
          >
            <a-select-option
              v-for="model in availableModelStore.llmAvailableModelCfg"
              :key="model.id"
              :value="model.id"
            >
              {{ model.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="系统提示" name="system_prompt">
          <!-- <a-textarea v-model:value="CreateConversationForm.system_prompt" :rows="4" /> -->
          <MonacoEditor
            v-model:modelValue="CreateConversationForm.system_prompt"
            language="markdown"
            style="height: 100px;"
            :editorOptions="{
              theme: 'vs',
              fontSize: 12,
              minimap: { enabled: false },
              lineNumbers: 'off',
              wordWrap: 'on',
              renderWhitespace: 'selection',
              quickSuggestions: false,
              links: true,
              autoClosingBrackets: 'never',
              autoIndent: 'keep'
            }"
          />
        </a-form-item>
        <a-form-item label="温度">
          <div class="slider-container">
            <a-slider
              v-model:value="CreateConversationForm.temperature"
              :min="0.1"
              :max="2"
              :step="0.1"
              :tooltip-formatter="value => `${value.toFixed(1)}`"
              style="flex: 1;"
            />
            <div class="value-display">
              {{ CreateConversationForm.temperature !== undefined ? CreateConversationForm.temperature.toFixed(1) : '0.0' }}
            </div>
          </div>
        </a-form-item>
        <a-form-item label="知识库">
          <a-select
            v-model:value="CreateConversationForm.knowledge_base_ids"
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
        <!-- 新增 MCP 集成 -->
        <a-form-item label="MCP服务">
          <a-select
            v-model:value="CreateConversationForm.selectedMcpServices"
            mode="multiple"
            placeholder="请选择MCP服务"
            option-label-prop="label"
          >
            <a-select-option
              v-for="option in mcpServerOptions"
              :key="option.key"
              :value="option.key"
            >
              {{ option.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <!-- 新增 use_memory 开关 -->
        <a-form-item label="启用记忆" name="use_memory">
          <t-switch size="large" v-model="CreateConversationForm.use_memory" />
        </a-form-item>
      </a-form>
      <template #footer>
        <t-button theme="default" @click="handleModalClose" style="margin-right: 10px">取消</t-button>
        <t-button theme="primary" @click="handleConversationSubmit">
          {{ isEditing ? '更新' : '创建' }}
        </t-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">

import { ref, onMounted, computed, watch, h, nextTick } from 'vue';
import { useMcpStore } from '@/store/mcpStore'


import {
  Chat as TChat,
  ChatAction as TChatAction,
  ChatContent as TChatContent,
  ChatSender as TChatSender,
  ChatItem as TChatItem,
  ChatReasoning as TChatReasoning,
  ChatLoading as TChatLoading
} from '@tdesign-vue-next/chat';
import { 
  SystemSumIcon, 
  ArrowDownIcon, 
  CheckCircleIcon, 
  CloseIcon 
} from 'tdesign-icons-vue-next';
import { 
  Button as TButton, 
  MessagePlugin 
} from 'tdesign-vue-next';

import {
  message,
  Modal as AModal,
  Form as AForm,
  Input as AInput,
  Select as ASelect,
  Slider as ASlider,
  Menu as AMenu,
  Spin as ASpin,
  Switch as ASwitch, // 引入 Switch 组件
  theme
} from 'ant-design-vue';
import {
  DeleteOutlined,
  EditOutlined,
  CommentOutlined,
} from '@ant-design/icons-vue';
import {
  createConversation,
  listConversations,
  deleteConversation,
  updateConversation,
  clearMessageHistory,
  getMessageHistory,
  sendMessage
} from '@/api/conversation';
import { listKnowledge } from '@/api/knowledge';
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import SourceCard from '@/components/SourceCard.vue';
import ToolCallCard from '@/components/ToolCallCard.vue'


import type { Key } from 'ant-design-vue/es/_util/type';



interface ExtendedChatMessage {
  content: any;
  role: 'user' | 'assistant' | 'tool';
  image_url?: any; // 用于前端图片显示
  name?: any
  avatar?: any
  source: any;
  status?: 'loading' | 'error' | 'success';
  timestamp: number;
  tool_calls?: any
  tool_call_id?: any
  datetime?: any
  reasoning?: any
}

interface StreamMessage {
  event: 'START' | 'MESSAGE' | 'SOURCE' | 'END' | 'ERROR' | 'TOOL_START' | 'TOOL_END';
  text?: string;
  [key: string]: any;
}

// 定义更具体的 API 参数类型
interface CreateConversationParams extends Api.BaseConversationParams {
  use_memory: boolean;
  conv_id: string;
  model: any;
  selectedMcpServices: []; // 用于表单绑定的选中项
  mcp_server_configs: null; // 用于API提交的配置
}


const roleConfig = ref({
  user: {
    name: '我',
    // avatar: 'src/assets/human.svg'
    avatar: 'https://tdesign.gtimg.com/site/avatar.jpg'
  },
  assistant: {
    name: '助手',
    // avatar: 'src/assets/bot.svg'
    avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png'
  },
  tool: {
    name: '工具',
    avatar: 'src/assets/tool.svg'
  }
});

const query = ref('');

const availableModelStore = useAvailableModelStore();
const mcpStore = useMcpStore()
const { token } = theme.useToken();
// MCP
// 新增计算属性 - MCP服务选项
const mcpServerOptions = computed(() => {
  return Object.entries(mcpStore.parsedMcpServers).map(([key, config]) => ({
    key,
    name: key,
    value: config
  }))
})

// 表单数据
const CreateConversationForm = ref<CreateConversationParams>({ // 使用扩展后的接口
  title: '新渠道',
  system_prompt: '# 角色\n我是由`ReadBetween`构建的智能助理。\n\n# 要求\n- 严格按照用户要求回复问题。\n- 遵循社会主义核心价值观。\n',
  model: availableModelStore.llmAvailableModelCfg && availableModelStore.llmAvailableModelCfg.length > 0 ? availableModelStore.llmAvailableModelCfg[0].id : null, 
  temperature: 0.3,
  knowledge_base_ids: [],
  use_memory: true, // 默认启用记忆
  conv_id: "",
  selectedMcpServices: [], // 用于MCP表单绑定的选中项
  mcp_server_configs: null, // 用于MCP-API提交的配置
});
// 状态管理
const activeKey = ref<string[]>([]);
const conversation_items = ref([]);
const chatsList = ref<ExtendedChatMessage[]>([]);
const toolCallsList = ref<ExtendedChatMessage[]>([]); // 完整的不进行任何过滤的chatsList 为了配合工具卡片展示
const knowledgeList = ref([]);
const isCreateDialogVisible = ref(false);
const isEditing = ref(false);
const isStreamLoading = ref(false); // stream是否结束
const isNewMsgLoading = ref(false); // 新消息是否处于加载状态
// 动态计算 clearHistory 的值
const showclearHistory = computed(() => {
  return chatsList.value.length > 1;
});

// 存储图片尺寸信息
const imageDimensions = ref({})

// 根据图片尺寸决定显示宽度
const imageWidth = (url) => {
  const dimensions = imageDimensions.value[url]
  if (dimensions && dimensions.height > dimensions.width * 1.5) {
    return '60%'
  }
  return '80%'
}

// 图片加载完成回调
const onImageLoad = (event) => {
  const img = event.target
  imageDimensions.value[img.src] = {
    width: img.naturalWidth,
    height: img.naturalHeight
  }
}

// 屏幕滚动
const chatRef = ref(null);
const isShowToBottom = ref(false);
// 滚动到底部
const backBottom = () => {
  chatRef.value.scrollToBottom({
    behavior: 'smooth',
  });
};
// 是否显示回到底部按钮
const handleChatScroll = function ({ e }) {
  const scrollTop = e.target.scrollTop;
  isShowToBottom.value = scrollTop > 200 && scrollTop < 1000;
};

// 查找对应的tool call
const findToolCall = (toolCallId: string) => {
  // 遍历所有消息找到对应的tool call
  for (const msg of toolCallsList.value) {
    if (msg.tool_calls && Array.isArray(msg.tool_calls)) {
      const found = msg.tool_calls.find(tc => tc.id === toolCallId)
      if (found) {
        return found
      }
    }
  }
  return null
}

// 获取会话列表
const fetchConversations = async () => {
  try {
    const res = await listConversations();
    if (res.data.status_code === 200) {
      conversation_items.value = res.data.data.data;
    }
  } catch (error) {
    message.error('获取会话列表失败');
  }
};

// 格式化 datetime，精确到秒
const formatDateTime = (date) => {
  const today = new Date();
  const messageDate = new Date(date);

  // 判断是否是今日消息
  if (
    messageDate.getFullYear() === today.getFullYear() &&
    messageDate.getMonth() === today.getMonth() &&
    messageDate.getDate() === today.getDate()
  ) {
    // 今日消息，显示 "今日 HH:mm"
    return `今日 ${String(messageDate.getHours()).padStart(2, '0')}:${String(messageDate.getMinutes()).padStart(2, '0')}`;
  }

  // 判断是否是今年消息
  if (messageDate.getFullYear() === today.getFullYear()) {
    // 今年消息，显示 "MM-DD HH:mm"
    return `${String(messageDate.getMonth() + 1).padStart(2, '0')}-${String(messageDate.getDate()).padStart(2, '0')} ${String(messageDate.getHours()).padStart(2, '0')}:${String(messageDate.getMinutes()).padStart(2, '0')}`;
  }

  // 不是今年消息，显示 "YYYY-MM-DD HH:mm"
  return `${String(messageDate.getFullYear()).padStart(4, '0')}-${String(messageDate.getMonth() + 1).padStart(2, '0')}-${String(messageDate.getDate()).padStart(2, '0')} ${String(messageDate.getHours()).padStart(2, '0')}:${String(messageDate.getMinutes()).padStart(2, '0')}`;
};

// 获取消息历史
const fetchMessageHistory = async (convId: string) => {
  try {
    const res = await getMessageHistory({ conv_id: convId });
    if (res.data.status_code === 200) {

      // 配合工具卡片查找调用信息
      toolCallsList.value = res.data.data
      .filter(msg => {  // 过滤掉助手tool_calls不为空，且content为空的消息
          return (msg.role === "assistant" && msg.tool_calls && msg.tool_calls.length > 0);
        })
      .map(msg => ({
        content: JSON.parse(msg.content),
        role: msg.role || null,
        name: roleConfig.value[msg.role].name, // 根据角色获取配置中的 name
        avatar: roleConfig.value[msg.role].avatar, // 根据角色获取配置中的 avatar
        source: JSON.parse(msg.source),
        tool_call_id: msg.tool_call_id,
        tool_calls: JSON.parse(msg.tool_calls),
        timestamp: new Date(msg.timestamp).getTime(),
        datetime: formatDateTime(new Date(msg.timestamp))
      }));


      chatsList.value = res.data.data
      .filter(msg => {  // 过滤掉助手tool_calls不为空，且content为空的消息
          const content = JSON.parse(msg.content || "null"); // 如果 content 不存在或为空，解析为 null
          return !(msg.role === "assistant" && (!content || content === ""));
        })
      .map(msg => {
          let parsedContent;
          try {
            parsedContent = JSON.parse(msg.content);
          } catch (e) {
            parsedContent = msg.content; // 如果解析失败，使用原始内容
          }

          // 处理content，确保最终是字符串
          let finalContent = '';
          let imageUrl = null; // 存储图片URL用于页面显示
          if (Array.isArray(parsedContent)) {  // 处理多模态问答对
            // 处理多部分内容（text + image_url等）
            finalContent = parsedContent.map(part => {
              if (part.type === 'text') {
                return part.text;
              } else if (part.type === 'image_url') {
                imageUrl = part.image_url.url;
              }
              return '';
            }).join('\n\n');
          } else if (typeof parsedContent === 'string') {  // 处理普通问答对
            // 已经是字符串，直接使用
            finalContent = parsedContent;
          } else {
            // 其他情况转为字符串
            finalContent = JSON.stringify(parsedContent);
          }

          // 提取<think>和</think>之间的内容作为reasoningContent
          let reasoningContent = null;
          const thinkTagRegex = /<think>(.*?)<\/think>/s;
          const thinkMatch = finalContent.match(thinkTagRegex);
          if (thinkMatch && thinkMatch[1]) {
            reasoningContent = thinkMatch[1].trim();
          }
          // 移除<think>和</think>之间的内容作为finalContent
          finalContent = finalContent.replace(thinkTagRegex, '').trim();

          return {
            content: finalContent,
            reasoning: reasoningContent,
            image_url: imageUrl,
            role: msg.role || null,
            name: roleConfig.value[msg.role].name, // 根据角色获取配置中的 name
            avatar: roleConfig.value[msg.role].avatar, // 根据角色获取配置中的 avatar
            source: JSON.parse(msg.source),
            tool_call_id: msg.tool_call_id,
            tool_calls: JSON.parse(msg.tool_calls),
            timestamp: new Date(msg.timestamp).getTime(),
            datetime: formatDateTime(new Date(msg.timestamp))
          };
        });
      console.log(chatsList.value)
      console.log(toolCallsList.value)
    }
    else {
      console.error('获取消息历史失败:', res.data); // 打印错误信息
      message.error('获取消息历史失败');
      chatsList.value = []; // 出错时，确保 chats.value 仍然是空数组或数组
    }
  } catch (error) {
    console.error('获取消息历史异常:', error); // 打印异常信息
    message.error('获取消息历史失败');
    chatsList.value = []; // 异常时，确保 chats.value 仍然是空数组或数组
  }
};

// 获取知识库列表
const fetchKnowledgeList = async () => {
  try {
    const res = await listKnowledge({
      page: 1,
      size: 1000 // 随便给一个大的值 以后再增加全量接口
    });
    if (res.data.status_code === 200) {
      knowledgeList.value = res.data.data.data;
    }
  } catch (error) {
    message.error('获取知识库失败');
  }
};

// 文件（图片、附件）上传相关
interface UploadFile {
  uid: string;
  name: string;
  status: 'uploading' | 'done' | 'error';
  url?: string;
  type?: string;
  size?: number;
  response?: any;
}

// 已上传的图片文件列表
const uploadedImageFiles = ref<any[]>([]);
// 图片上传配置
const MAX_FILE_SIZE_KB = 10 * 1024;
const MAX_FILE_COUNT = 1;
const imageUploadProps = ref({
  accept: 'image/*', // 接受所有图片类型
  multiple: false, // 根据你的需求设置是否允许多文件上传
} as any);
// 附件上传配置 
const attachmentUploadProps = ref({
  accept: '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar', // 支持的文件类型
  multiple: true,
});

const handleFileUpload = async (params: { files: File[]; name }) => {
  if (params.name === 'uploadImage') {
    console.log('图片上传逻辑 (Base64)', params);

    // 1. 检查文件数量
    if (params.files.length > MAX_FILE_COUNT || uploadedImageFiles.value.length + params.files.length > MAX_FILE_COUNT) {
      MessagePlugin.error(`最多允许上传 ${MAX_FILE_COUNT} 张图片!`);
      return;
    }

    // 2. 验证并处理每个文件
    for (const file of params.files) {
      // 2.1 验证文件类型
      if (!file.type.startsWith('image/')) {
        MessagePlugin.error(`${file.name} 不是图片文件!`);
        continue; // 跳过非图片文件
      }

      // 2.2 验证文件大小
      const isLtMaxSize = file.size / 1024 <= MAX_FILE_SIZE_KB;
      if (!isLtMaxSize) {
        MessagePlugin.error(`${file.name} 大小不能超过 ${MAX_FILE_SIZE_KB / 1024}MB!`);
        continue; // 跳过超大文件
      }

      // 2.3 创建文件包装器并立即显示
      const fileWrapper = {
        name: file.name,
        status: 'progress' as const,
        uid: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file: file,
        preview: URL.createObjectURL(file) // 用于即时预览
      };
      uploadedImageFiles.value.push(fileWrapper);

      // 2.4 异步转换为 Base64
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // 找到对应的文件并更新
        const targetFile = uploadedImageFiles.value.find(f => f.uid === fileWrapper.uid);
        if (targetFile) {
          targetFile.status = 'success';
          targetFile.url = reader.result as string;
          targetFile.type = file.type;
          URL.revokeObjectURL(targetFile.preview); // 释放内存
          targetFile.preview = null;
        }
        MessagePlugin.success(`${file.name} 加载成功`);
      };
      reader.onerror = (error) => {
        console.error('Base64 conversion error:', error);
        const targetFile = uploadedImageFiles.value.find(f => f.uid === fileWrapper.uid);
        if (targetFile) {
          targetFile.status = 'fail';
          targetFile.error = '文件读取失败';
        }
        MessagePlugin.error(`${file.name} 加载失败`);
      };
    }
  } else if (params.name === 'uploadAttachment') {
    console.log('附件上传逻辑', params);
  }
};
// 获取图片预览
const getImagePreview = (file) => {
  return file.url || file.preview;
}
// 新增移除图片方法
const removeImage = (index) => {
  uploadedImageFiles.value.splice(index, 1);
};

const onFileSelect = (params: { files: File[]; name }) => {
  if (params.files.length === 0) return;
  // 仅做日志记录 由action实现上传逻辑
  if (params.name === 'uploadImage') {
    console.log('选择了图片文件:', params.files);
  } else if (params.name === 'uploadAttachment') {
    console.log('选择了附件文件:', params.files);
  }
};

// 联网搜索
const isSearchEnabled = ref(false);
const toggleSearch = () => {
  isSearchEnabled.value = !isSearchEnabled.value;
  console.log(isSearchEnabled.value)
}


const handleMessageSend = async (user_message: any) => {
  if (!activeKey.value[0] || !user_message.trim()) return;
  try {
    isStreamLoading.value = true;
    isNewMsgLoading.value = true;
    
    
    
    // ================= 用户输入处理阶段 =================
    // 构建消息内容
    let contentArray: Array<{ type: string; text?: string; image_url?: { url: string } }> = [];
    
    // 添加已上传的图片
    console.log('上传图片文件：', uploadedImageFiles.value)
    let multimodel_content
    let multimodel_image_url
    uploadedImageFiles.value.forEach(file => {
      // console.log(file.url)
      // console.log(file.type?.startsWith('image/'))
      if (user_message.trim()) {
        contentArray.push({ type: "text", text: user_message });
        multimodel_content = user_message
      }
      if (file.url && file.type?.startsWith('image/')) {
        contentArray.push({
          type: "image_url",
          image_url: { url: file.url }
        });
        multimodel_image_url = file.url 
      }
      // 修改文本问答为多模态问答
      user_message = contentArray
    })


    // ================= 消息创建阶段 =================
    // 创建完全独立的消息对象
    let now_datetime = Date.now()
    const userMessage: ExtendedChatMessage = {
      content: (typeof user_message === 'object') ? multimodel_content : user_message,  // 使用原始输入文本
      image_url: (typeof user_message === 'object') ? multimodel_image_url : null,
      role: 'user',
      name: roleConfig.value['user'].name,
      avatar: roleConfig.value['user'].avatar,
      source: [],
      timestamp: now_datetime,
      datetime: formatDateTime(now_datetime)
    };
    console.log(userMessage)

    const assistantMessage: ExtendedChatMessage = {
      content: '',
      reasoning: '',
      role: 'assistant',
      status: 'loading',
      name: roleConfig.value['assistant'].name,
      avatar: roleConfig.value['assistant'].avatar,
      source: [],
      timestamp: userMessage.timestamp + 3,  // 确保唯一性
      datetime: formatDateTime(userMessage.timestamp + 3)
    };

    // 不可变更新消息列表
    chatsList.value = [
      ...chatsList.value,
      userMessage,          // 用户消息固定不变
      assistantMessage      // 助手消息单独更新
    ];

    // 滚动到底部
    nextTick(() => {
      chatRef.value?.scrollToBottom({ behavior: 'smooth' });
    });

    // ================= 流处理阶段 =================
    const response = await sendMessage({
      conv_id: activeKey.value[0],
      message: JSON.stringify(user_message),        // 使用原始输入文本
      search: isSearchEnabled.value,
      temperature: CreateConversationForm.value.temperature
    });

    // 情况 query 用户发送的文本内容
    query.value = ""
    // 清空 uploadedFiles 文件上传列表
    uploadedImageFiles.value = [];

    if (!response.ok) throw new Error('Failed to get stream');
    // 检查响应头
    // console.log('Content-Type:', response.headers.get('Content-Type'));
    // console.log('Transfer-Encoding:', response.headers.get('Transfer-Encoding'));

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

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

          const chunkText = decoder.decode(value);
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
          if (currentContent.length > 0){
            isNewMsgLoading.value = false; // 开始输出新消息 取消加载状态
          }
          // console.log(currentContent)
          updateAssistantContent(currentContent);
          // 每次收到消息都滚动到底部
          nextTick(() => {
            chatRef.value?.scrollToBottom({ behavior: 'auto' });
          });
          break;

        case 'SOURCE':
          // console.log('Source data:', data.extra);
          const sourceData = data.extra;
          handleSourceData(sourceData)
          break;

        case 'END':
          handleStreamEnd();
          break;
        
        case 'ERROR':
          handleStreamError(data.text);
          break;
        
        case 'TOOL_START':
          const toolStartData = data.extra;
          handleToolStart(toolStartData);
          break;
        
        case 'TOOL_END':
          const toolEndData = data.extra;
          handleToolEnd(toolEndData);
          break;
      }
    };

    // ================= 关键更新方法 =================
    const updateAssistantContent = (content: string) => {
      // 获取最后一条消息
      const lastMessageIndex = chatsList.value.length - 1;

      // 解析content，提取thinking和普通内容
      let thinkingContent = '';
      let normalContent = '';

      // 临时变量用于跟踪是否在think标签内
      let inThinkTag = false;
      let buffer = '';

      for (let i = 0; i < content.length; i++) {
        // 检查是否遇到<think>开始标签
        if (content.substr(i, 7) === '<think>' && !inThinkTag) {
          inThinkTag = true;
          i += 6; // 跳过标签
          continue;
        }
        
        // 检查是否遇到</think>结束标签
        if (content.substr(i, 8) === '</think>' && inThinkTag) {
          inThinkTag = false;
          thinkingContent += buffer;
          buffer = '';
          i += 7; // 跳过标签
          continue;
        }
        
        // 根据当前状态积累内容
        if (inThinkTag) {
          buffer += content[i];
        } else {
          normalContent += content[i];
        }
      }
      
      // 如果think标签未关闭，把buffer内容加到thinkingContent
      if (inThinkTag) {
        thinkingContent += buffer;
      }

      // 检查最后一条消息是否存在且 role 是否为 "assistant"
      if (lastMessageIndex >= 0 && chatsList.value[lastMessageIndex].role === "assistant") {
        // 仅更新最后一条消息的内容和状态
        chatsList.value = chatsList.value.map((msg, index) => {
          if (index === lastMessageIndex) {
            // 如果是最后一条消息且 role 为 "assistant"，则更新内容和状态
            return {
              ...msg,
              content: normalContent,
              reasoning: thinkingContent || msg.reasoning, // 保留已有的reasoning如果没有新的thinking内容
              status: content ? 'success' : 'loading'
            };
          }
          return msg; // 保持其他消息不变
        });
      } else {
        // 如果最后一条消息的 role 不是 "assistant"，创建新的助手消息
        let now_datetime = Date.now()
        const newAssistantMessage: ExtendedChatMessage = {
          content: normalContent,
          reasoning: thinkingContent,
          role: 'assistant',
          status: 'loading',
          name: roleConfig.value['assistant'].name,
          avatar: roleConfig.value['assistant'].avatar,
          source: [],
          timestamp:now_datetime,  // 确保唯一性
          datetime: formatDateTime(now_datetime)
        };

        chatsList.value = [
          ...chatsList.value,
          newAssistantMessage      // 更新二次调用的助手消息单
        ];
        
      }
    };
  // ================= 处理工具开始调用事件 =================
  const handleToolStart = (toolStartData: any) =>  {
    // 向 chats 列表中插入一条新消息
    // 获取所有的工具名称
    const toolNames = toolStartData.map(tool => tool.function.name).join('，') || '未知工具';
    let now_datetime = Date.now()
    const newAssistantCallToolMessage: ExtendedChatMessage = {
      role: "assistant",
      name: roleConfig.value['assistant'].name,
      avatar: roleConfig.value['assistant'].avatar,
      content: `正在调用工具：${toolNames}`,
      timestamp: now_datetime,
      datetime: formatDateTime(now_datetime),
      tool_calls: toolStartData,
      source: null
    };

    // 检查最后一条消息的 content 是否为空
    if (chatsList.value.length > 0 && !chatsList.value[chatsList.value.length - 1].content) {
      chatsList.value.pop(); // 删除最后一条消息（如果它的 content 为空）
    }

    // 将新消息 push 到 chats.value 中
    chatsList.value = [
      ...chatsList.value,
      newAssistantCallToolMessage
    ];
    // 记录工具调用信息
    toolCallsList.value = [
      ...toolCallsList.value,
      newAssistantCallToolMessage
    ]
    

  }
  // ================= 处理工具调用结束时间 =================   
  const handleToolEnd = (toolEndData: any) =>  {
    // 向 chats 列表中插入一条新消息
    let now_datetime = Date.now()
    const newToolMessage: ExtendedChatMessage = {
      role: "tool",
      tool_call_id: toolEndData.tool_call_id,
      content: toolEndData.content,
      source: null,
      name: roleConfig.value['tool'].name,
      avatar: roleConfig.value['tool'].avatar,
      timestamp: now_datetime,
      datetime: formatDateTime(now_datetime),
    };

    // 将新消息 push 到 chats.value 中
    chatsList.value = [
      ...chatsList.value,
      newToolMessage
    ];
  }
  // ================= 处理来源数据的方法 =================
  const handleSourceData = (sourceData: any) => {
    chatsList.value = chatsList.value.map(msg => {
      if (msg.timestamp === assistantMessage.timestamp) {
        // 遍历 sourceData 并根据 source 值添加 avatar 属性
        const processedCurrentSourceCard = sourceData.map((item) => {
          let faviconUrl = '';
          const urlObj = new URL(item.url);
          faviconUrl = `${urlObj.origin}/favicon.ico`;
          if (item.source === "kb") {
            return { ...item, avatar: faviconUrl };
          } else if (item.source === "web") {
            return { ...item, avatar: faviconUrl };
          }
          return item;
        });

        return {
          ...msg,
          source: [...msg.source, ...processedCurrentSourceCard]
        };
      }
      return msg;
    });
  };

    // ================= 结束处理 =================
    const handleStreamEnd = () => {
      isStreamEnded = true;
      isStreamLoading.value = false;
      reader.cancel();

      // 最终状态更新
      chatsList.value = chatsList.value.map(msg => {
        if (msg.timestamp === assistantMessage.timestamp) {
          return { ...msg, status: undefined };
        }
        return msg;
      });
    };

    // ================= 错误处理 =================
    const handleStreamError = (error: any) => {
      console.error('Stream error:', error);
      message.error('消息处理失败');
      isNewMsgLoading.value = false
      isStreamLoading.value = false

      // 只修改当前助手消息状态
      chatsList.value = chatsList.value.map(msg => {
        if (msg.timestamp === assistantMessage.timestamp) {
          return { ...msg, status: 'error' };
        }
        return msg;  // 用户消息保持原样
      });
      
      // 3秒后自动删除错误消息
      setTimeout(() => {
        chatsList.value = chatsList.value.filter(msg => 
          msg.timestamp !== assistantMessage.timestamp
        );
      }, 3000);

    };

    await processStream();
  } catch (error) {
    console.error('Message send error:', error);
    isStreamLoading.value = false
    isNewMsgLoading.value = false
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
    chatsList.value = [];
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
      chatsList.value = [];
    }
  } catch (error) {
    message.error('删除会话失败');
  }
};

// 编辑会话
const handleEdit = (item) => {
  isEditing.value = true;
  isCreateDialogVisible.value = true;

  // 提取 knowledge_bases 中每个元素的 id
  const knowledgeBaseIds = item.knowledge_bases.map((kb) => kb.id);
  // 查找匹配的模型对象，使用 available_model_id 进行匹配
  const selectedModel = availableModelStore.llmAvailableModelCfg.find(model => model.id === item.available_model_id);
  
  // 处理MCP服务回显
  const selectedMcpKeys = item.selected_mcp_servers 
    ? Object.keys(item.selected_mcp_servers)
    : [];
  // 处理MCP服务配置 - 保留原始配置
  const mcpServerConfigs = item.selected_mcp_servers || null;

  CreateConversationForm.value = {
    title: item.title,
    model: selectedModel?.id || null,  // 使用 id 而不是 name
    system_prompt: item.system_prompt,
    temperature: item.temperature,
    knowledge_base_ids: knowledgeBaseIds,
    conv_id: item.id,
    use_memory: !!item.use_memory, // 同步 use_memory 字段
    selectedMcpServices: selectedMcpKeys, // 用于回显选中的key
    mcp_server_configs: mcpServerConfigs // 保留原始配置
  } as CreateConversationParams; // 强制类型转换
};

// 提交会话创建/更新
const handleConversationSubmit = async () => {
  try {
    if (!CreateConversationForm.value.model) {
      message.error('请选择模型'); // 提示用户选择模型
      return;
    }

    // 准备MCP服务配置
    const selectedMcpConfigs = {};
    CreateConversationForm.value.selectedMcpServices.forEach(key => {
      const option = mcpServerOptions.value.find(opt => opt.key === key);
      if (option) {
        selectedMcpConfigs[option.name] = option.value;
      }
    });

    // 使用对象解构排除 model 字段
    const { model, ...rest } = CreateConversationForm.value;
    console.log(CreateConversationForm.value)
    const submitForm = {
      ...rest,
      available_model_id: model,  // 直接使用 model 值，因为它已经是 id
      use_memory: CreateConversationForm.value.use_memory ? 1 : 0, // Convert boolean to 1 or 0
      mcp_server_configs: Object.keys(selectedMcpConfigs).length > 0 
        ? selectedMcpConfigs 
        : null
    };

    if (isEditing.value) {
      await updateConversation(submitForm as Api.UpdateConversationParams); // 强制类型转换
      message.success('会话更新成功');
    } else {
      await createConversation(submitForm as Api.CreateConversationParams);
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
  CreateConversationForm.value = {
    title: '新渠道',
    model: availableModelStore.llmAvailableModelCfg && availableModelStore.llmAvailableModelCfg.length > 0 ? availableModelStore.llmAvailableModelCfg[0].id : null,
    system_prompt: '# 角色\n我是由`ReadBetween`构建的智能助理。\n\n# 要求\n- 严格按照用户要求回复问题。\n- 遵循社会主义核心价值观。\n',
    temperature: 0.3,
    knowledge_base_ids: [],
    use_memory: true, // 初始化 use_memory 为 true
    conv_id: "",
    mcp_server_configs: null, // 重置MCP服务配置
    selectedMcpServices: [] // 重置选中项
  };
};


// 会话点击处理
const handleConversationClick = async (info: { key: Key }) => {
  activeKey.value = [info.key.toString()]; // 确保转换为字符串
  console.log('Selected:', info.key);
  await fetchMessageHistory(info.key.toString());
};

// 初始化
onMounted(async () => {
  await fetchConversations();
  await fetchKnowledgeList();
  await mcpStore.fetchData()
  await availableModelStore.loadAvailableModelCfg();
});

// 监听模型配置变化
watch(() => availableModelStore.llmAvailableModelCfg, (newVal) => {
  if (newVal && newVal.length > 0 && !CreateConversationForm.value.model) {
    CreateConversationForm.value.model = newVal[0].id;
  }
}, { immediate: true });
</script>

<style scoped>
.chat-image-container {
  margin: 12px 0;
  display: flex;
  justify-content: center;
  width: 100%;
}

.chat-image {
  max-width: 80%; /* 默认宽度 */
  max-height: 400px; /* 控制最大高度 */
  border-radius: 8px;
  object-fit: contain;
  background-color: var(--td-bg-color-secondarycontainer);
  border: 1px solid var(--td-border-level-1-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-image {
    max-width: 100%;
    max-height: 300px;
  }
}

/* 悬停效果 */
.chat-image:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
::-webkit-scrollbar-thumb {
  background-color: var(--td-scrollbar-color);
}
::-webkit-scrollbar-thumb:horizontal:hover {
  background-color: var(--td-scrollbar-hover-color);
}
::-webkit-scrollbar-track {
  background-color: var(--td-scroll-track-color);
}

.chat-box {
  position: relative;
  .bottomBtn {
    position: absolute;
    left: 50%;
    margin-left: -20px;
    bottom: 210px;
    padding: 0;
    border: 0;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    box-shadow: 0px 8px 10px -5px rgba(0, 0, 0, 0.08), 0px 16px 24px 2px rgba(0, 0, 0, 0.04),
      0px 6px 30px 5px rgba(0, 0, 0, 0.05);
  }
  .to-bottom {
    width: 60px;
    height: 60px;
    border: 1px solid #dcdcdc;
    box-sizing: border-box;
    background: var(--td-bg-color-container);
    border-radius: 50%;
    font-size: 24px;
    line-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    .t-icon {
      font-size: 24px;
    }
  }
}
.chat-sender {
  .btn {
    color: var(--td-text-color-disabled);
    border: none;
    &:hover {
      color: var(--td-brand-color-hover);
      border: none;
      background: none;
    }
  }
  .btn.t-button {
    height: var(--td-comp-size-m);
    padding: 0;
  }
  .model-select {
    display: flex;
    align-items: center;
    .t-select {
      width: 112px;
      height: var(--td-comp-size-m);
      margin-right: var(--td-comp-margin-s);
      .t-input {
        border-radius: 32px;
        padding: 0 15px;
      }
      .t-input.t-is-focused {
        box-shadow: none;
      }
    }
    .check-box {
      width: 112px;
      height: var(--td-comp-size-m);
      border-radius: 32px;
      border: 0;
      background: var(--td-bg-color-component);
      color: var(--td-text-color-primary);
      box-sizing: border-box;
      flex: 0 0 auto;
      .t-button__text {
        display: flex;
        align-items: center;
        justify-content: center;
        span {
          margin-left: var(--td-comp-margin-xs);
        }
      }
    }
    .check-box.is-active {
      border: 1px solid var(--td-brand-color-focus);
      background: var(--td-brand-color-light);
      color: var(--td-text-color-brand);
    }
  }
}

.aside {
  background-color: var(--td-bg-color-container);
  overflow: auto;
  height: 100%;
  border-right: 1px solid var(--td-component-stroke);
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

.read-between-placeholder {
  font-size: 96px; /* Adjust as needed */
  color: #999; /* Adjust as needed */
  text-align: center;

  /* Make it fill the parent container */
  width: 100%;
  height: 100%;

  /* Center the text both horizontally and vertically */
  display: flex;
  justify-content: center; /* Horizontal centering */
  align-items: center;     /* Vertical centering */

  /* Font adjustments */
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; /* A common sans-serif stack */
  font-weight: 400; /* Light or Regular, try 300 or 400 */
}

/* 图片预览容器样式 - 移除上传状态相关样式 */
.image-preview-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding: 8px;
  background: var(--td-bg-color-secondarycontainer);
  border-radius: 8px;
  border: 1px dashed var(--td-border-level-2-color);
}

/* 单个预览项基础样式 */
.image-preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--td-border-level-1-color);
}

/* 只有正在上传的图片才置灰 */
.image-preview-item.is-uploading {
  opacity: 0.7;
  filter: grayscale(50%);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 上传指示器样式 */
.upload-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.2);
  color: white;
  font-size: 12px;
}

.upload-text {
  margin-top: 4px;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}

/* 解决思考中内容空白间隙问题 */
:deep(.t-chat__text__assistant) p,
:deep(.t-chat__text__assistant) ul,
:deep(.t-chat__text__assistant) ol {
    margin: 0;
    line-height: 1.5;
}
</style>