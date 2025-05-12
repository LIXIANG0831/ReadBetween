<template>
  <div class="common-layout">
    <a-layout style="height: 100vh;">
      <a-layout-sider width="250px" class="aside" style="height: 100%;margin-bottom: 16px;">
        <div style="padding: 16px;height: 100%;display: flex;flex-direction: column;">

          <a-menu
            v-model:selectedKeys="activeKey"
            mode="inline"
            :style="style"
            @click="handleConversationClick"
          >
            <a-button type="primary" @click="isCreateDialogVisible = true" style="width: 200px;margin-bottom: 16px;">
              新建渠道
            </a-button>
            <a-menu-item v-for="item in conversation_items" :key="item.id" class="menu-item">
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
          <div v-if="activeKey.length > 0" style="width: 100%;">
              <!-- <div style="margin-bottom: 16px;">
                <a-button @click="handleClearHistory" :disabled="!activeKey[0]">
                  清除历史记录
                </a-button>
              </div> -->
              <Chat
              :chats="chats"
              @message-send="handleMessageSend"
              :message-key="msg => msg.timestamp.toString()"
              :loading="isLoading"
              :roleConfig="roleConfig"
              showClearContext
              :style="commonChatOuterStyle"
              :onClear="handleClearHistory"
              :chatBoxRenderConfig="chatBoxConfig"
              :renderInputArea="renderCustomInput"
              :uploadProps="customUploadProps"
              />
            </div>
          <div v-else class="read-between-placeholder">
            ReadBetween
          </div>


          <!-- <div style="padding: 16px;"> -->
            <!-- <div style="margin-bottom: 16px;">
              <a-button @click="handleClearHistory" :disabled="!activeKey[0]">
                清除历史记录
              </a-button>
            </div> -->


          <!-- </div> -->
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
      <a-form :model="CreateConversationForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="会话标题" name="title">
          <a-input v-model:value="CreateConversationForm.title" placeholder="请输入会话标题" />
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
          <a-textarea v-model:value="CreateConversationForm.system_prompt" :rows="4" />
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
        <!-- 新增 use_memory 开关 -->
        <a-form-item label="启用记忆" name="use_memory">
          <a-switch v-model:checked="CreateConversationForm.use_memory" />
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

import { Chat, Button, MarkdownRender } from '@kousum/semi-ui-vue';
import { ref, onMounted, computed, watch, h } from 'vue';
import {
  message,
  Modal as AModal,
  Form as AForm,
  Input as AInput,
  Select as ASelect,
  Slider as ASlider,
  Menu as AMenu,
  Spin as ASpin,
  Switch as ASwitch // 引入 Switch 组件
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
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import SourceCard from '@/components/SourceCard.vue';
// import ChatInput from '@/components/ChatInput.vue';
import { IconGlobeStroke } from '@kousum/semi-icons-vue';
import escapeHtml from 'escape-html';


interface ExtendedChatMessage {
  content: any;
  role: 'user' | 'assistant';
  source: any;
  status?: 'loading' | 'error';
  timestamp: number;
}

interface StreamMessage {
  event: 'START' | 'MESSAGE' | 'SOURCE' | 'END';
  text?: string;
  [key: string]: any;
}

// 定义更具体的 API 参数类型
interface CreateConversationParams extends Api.BaseConversationParams {
  use_memory: boolean;
  conv_id: string;
  model: any;
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



const availableModelStore = useAvailableModelStore();
const { token } = theme.useToken();

// 状态管理
const activeKey = ref<string[]>([]);
const conversation_items = ref([]);
const chats = ref<ExtendedChatMessage[]>([]);
const knowledgeList = ref([]);
const isCreateDialogVisible = ref(false);
const isEditing = ref(false);
const hints = ref<string[]>(["测试提示信息 1", "测试提示信息 2"]); // 初始化 hints 用于存储提示消息
let sourceContent = ''; // 来源信息
const isLoading = ref(false);


// 聊天框外边框属性设置
const commonChatOuterStyle = {
  border: '1px solid var(--semi-color-border)',
  borderRadius: '16px',
  height: '700px'
};

// 表单数据
const CreateConversationForm = ref<CreateConversationParams>({ // 使用扩展后的接口
  title: '新渠道',
  system_prompt: '你是我的AI助手',
  model: availableModelStore.llmAvailableModelCfg && availableModelStore.llmAvailableModelCfg.length > 0 ? availableModelStore.llmAvailableModelCfg[0].id : null, 
  temperature: 0.3,
  knowledge_base_ids: [],
  use_memory: true, // 默认启用记忆
  conv_id: ""
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
      conversation_items.value = res.data.data.data;
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
        content: JSON.parse(msg.content),
        role: msg.role === 'user' ? 'user' : 'assistant',
        source: JSON.parse(msg.source),
        timestamp: new Date(msg.timestamp).getTime()
      }));
      // console.log(chats.value)
    }
    else {
      console.error('获取消息历史失败:', res.data); // 打印错误信息
      message.error('获取消息历史失败');
      chats.value = []; // 出错时，确保 chats.value 仍然是空数组或数组
    }
  } catch (error) {
    console.error('获取消息历史异常:', error); // 打印异常信息
    message.error('获取消息历史失败');
    chats.value = []; // 异常时，确保 chats.value 仍然是空数组或数组
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

// 自定义提示信息
const renderHintBox = (props: { content: string, onHintClick: () => void, index: number }) => {
  console.log('renderHintBox called', props.content);
  const { content } = props; // 这里我们只需要 content，不需要 onHintClick 和 index
  const commonHintStyle = { // 可以复用你之前定义的样式，或者根据 sourceContent 的特点自定义样式
    border: '1px solid var(--semi-color-border)',
    padding: '10px',
    borderRadius: '10px',
    color: 'var( --semi-color-text-1)',
    display: 'block', // 修改为 block，让 sourceContent 独占一行
    cursor: 'default', // 修改 cursor 为 default，因为 sourceContent 通常不需要点击
    fontSize: '14px',
    marginTop: '8px', // 可以添加一些 margin，与聊天内容分隔开
    whiteSpace: 'pre-line' // 保留换行符，处理 sourceContent 中的换行
  };

  return h('div', { style: commonHintStyle}, content); // 使用 v-html 渲染 Markdown 内容
};



// 自定义文件上传
const uploadedFiles = ref<any[]>([]);
const MAX_FILE_SIZE_KB = 5 * 1024;
const MAX_FILE_COUNT = 5;
const customUploadProps = ref({
  action: 'https://picui.cn/api/v1/upload', // 你的图片上传接口地址
  name: 'file', // 对应接口文档中的 image 参数名
  accept: 'image/*', // 接受所有图片类型
  multiple: false, // 根据你的需求设置是否允许多文件上传
  // data: {}, // 如果需要额外的请求参数，在这里设置
  limit: MAX_FILE_COUNT,
  // maxSize: MAX_FILE_SIZE_KB,
  addOnPasting: true,
  headers: {
    'Authorization': `Bearer ${import.meta.env.VITE_IMAGE_BED_TOKEN}`,
    'Accept': 'application/json'
  }, // 如果需要自定义请求头，在这里设置
  onExceed: (fileList) => {
    message.error(`图片数量不能超过 ${MAX_FILE_COUNT}个!`);
  },
  // onSizeError: (file, fileList) => {
  //   message.error(`图片大小不能超过 ${MAX_FILE_SIZE_KB}KB!`);
  // },
  beforeUpload: (obj) => {
    // 上传实际接口之前
    console.log('beforeUpload:', obj);
    
    // 可以进行文件类型和大小的校验
    const fileType = obj.file.fileInstance.type; // 获取文件类型
    const fileSize = obj.file.fileInstance.size; // 获取文件大小（字节）
    
    const isLtMaxSize = fileSize / 1024 <= MAX_FILE_SIZE_KB;
    if (!isLtMaxSize) {
      message.error(`图片大小不能超过 ${MAX_FILE_SIZE_KB}KB!`);
      return { 
        shouldUpload: false, 
        fileInstance: obj.file.fileInstance, 
        autoRemove: true 
      }; // 返回对象，设置 autoRemove 为 true
    }
    return true;
  },
  afterUpload: (obj) => {
    // 上传实际接口之后
    console.log('afterUpload:', obj);
  },
  onChange: (info) => {
    // 过滤出状态为 'done' 的文件，更新 uploadedFiles
    uploadedFiles.value = info.fileList.filter(file => file.status === 'success');
  },
  onSuccess: (response, file, fileList) => {
    console.log('onSuccess:', response, file, fileList);
    if (response && response.status === true) {
      message.success(`${file.name} 上传成功.`);
      // 在这里处理上传成功后的逻辑，例如将返回的图片 URL 显示在聊天框中
      // 你可能需要更新你的 chats 状态，添加一条包含图片消息的新项
      const imageUrl = response.data.url; // 假设你的接口返回的 data.url 是图片地址
      // 注意：你需要根据你的聊天消息结构来添加这条图片消息
      // 例如：
      // chats.value = [
      //   ...chats.value,
      //   {
      //   role: 'user', // 或者 'assistant'，取决于谁发送的图片
      //   content: `![](${imageUrl})`, // 使用 Markdown 图片语法
      //   source: [],
      //   timestamp: Date.now(),
      //   },
      // ];
    } else {
      message.error(`${file.name} 上传失败.`);
    }
  },
  onError: (error, file, fileList) => {
    console.error('onError:', error, file, fileList);
    message.error(`${file.name} 上传失败.`);
  },
  onProgress: (percent, file) => {
    console.log(`${file.name} 上传中: ${percent}%`);
  },
  // 其他你可能需要的配置项...
} as any);

// 自定义对话框
const chatBoxConfig = ref({
  renderChatBoxContent: (props) => {
    const { role, message, defaultNode, className } = props;

    // 如果 message.status 是 "loading"，不返回任何内容 返回加载状态
    // message.content为空时 MarkdownRender会报错
    if (message.status === "loading" || message.content === "") {
      return h("div", { class: className, style: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40px' } }, [ // Center align the spin and set minHeight
        h(ASpin, { size: 'small' }) // Use ASpin for loading icon, size can be adjusted
      ]);
    }

    // 替换头像图标
    // 遍历 message.source，根据 source 字段添加 avatar 属性
    const processedHistorySourceCard = message.source && message.source.length > 0
      ? message.source.map((item) => {
        let faviconUrl = '';
      if (item.source === 'kb') {
        return { ...item, avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/root-web-sites/dy.png' };
      } else if (item.source === 'web') {
        // 截取网站域名
        const urlObj = new URL(item.url);
        faviconUrl = `${urlObj.origin}/favicon.ico`;
        return { ...item, avatar: faviconUrl };
      }
      return item; // 其他情况保持原样
    }) : [];

    // 处理多模态message响应
    let processedContent = '';
    if (Array.isArray(message.content)) {
      message.content.forEach(item => {
        if (item.type === 'text') {
          processedContent += item.text + '\n';
        } else if (item.type === 'image_url') {
          const imageUrl = item.image_url.url;
          processedContent += `![](${imageUrl})\n`;
        }
      });
    } else {
      processedContent = message.content;
    }

    // 使用 h 函数构建渲染内容
    const escapedContent = escapeHtml(processedContent);
    return h(
      'div',
      { class: className },
      message.source && message.source.length > 0
        ? [h(SourceCard, { source: processedHistorySourceCard }), h(MarkdownRender, { raw: escapedContent, components: {} })]
        : h(MarkdownRender, { raw: escapedContent, components: {} })
    );
  }
});

// 自定义输入区域渲染函数
const isSearchEnabled = ref(false);
const toggleSearch = () => isSearchEnabled.value = !isSearchEnabled.value;
const renderCustomInput = (props) => {
  return h('div', { style: { display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' } }, [
    // 默认输入框（占据剩余空间）
    h('div', { style: { flexGrow: 1 } }, [ // 使用 div 包裹 defaultNode 并设置 flexGrow
        props.defaultNode
    ]),

    // 网络搜索图标按钮
    h(Button, {
      type: isSearchEnabled.value ? 'primary' : 'default',
      onClick: toggleSearch,
      icon: () => h(IconGlobeStroke, { size: '32' }), // 使用 IconSearch 组件作为 icon
      style: {
        paddingRight: '8px',
        flexShrink: 0,
        padding: '6px',
        borderRadius: '50%',
        minWidth: 'unset',
        width: '48px',     // Fixed width and height for button size
        height: '48px',
        backgroundColor: 'var(--semi-color-fill-0)', // Default background
        border: 'none',
        display: 'flex',       // Ensure icon is centered
        alignItems: 'center',  // Vertically center icon
        justifyContent: 'center' // Horizontally center icon
      } // 调整图标按钮样式，去除文字部分的padding
    }),

    // 如果还有其他图标按钮，可以放在这里，例如：
    // h(Button, { ...otherButtonProps, icon: () => h(OtherIcon) }),
  ]);
};

// 发送消息处理
const handleMessageSend = async (user_message: any) => {
  if (!activeKey.value[0] || !user_message.trim()) return;
  try {
    isLoading.value = true;

    
    // 拼接UserMessage用于展示
    // 检查 uploadedFiles 是否为空
    if (uploadedFiles.value.length > 0) {
        // 构造包含图片的 userMessage
        const contentArray: Array<{ type: string; text?: string; image_url?: { url: string } }> = [
          { type: "text", text: user_message }
        ];

        uploadedFiles.value.forEach(file => {
          if (file.response?.data?.links?.url) {  // 校验响应存在
            let image_url = file.response.data.links.url
            contentArray.push({
              type: "image_url",
              image_url: { url: image_url }
            });
          }
        });
  
        // 修改为包含图片的 userMessage
        user_message = contentArray

    }

    // ================= 消息创建阶段 =================
    // 创建完全独立的消息对象
    const userMessage: ExtendedChatMessage = {
      content: user_message,  // 使用原始输入文本
      role: 'user',
      source: [],
      timestamp: Date.now()
    };

    const assistantMessage: ExtendedChatMessage = {
      content: '',
      role: 'assistant',
      status: 'loading',
      source: [],
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
      message: JSON.stringify(user_message),        // 使用原始输入文本
      search: isSearchEnabled.value,
      temperature: CreateConversationForm.value.temperature
    });

    // 清空 uploadedFiles 文件上传列表
    uploadedFiles.value = [];

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
          // console.log('Source data:', data.extra);
          const sourceData = data.extra;
          handleSourceData(sourceData)
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

  // ================= 处理来源数据的方法 =================
  const handleSourceData = (sourceData: any) => {
    chats.value = chats.value.map(msg => {
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
const handleEdit = (item) => {
  isEditing.value = true;
  isCreateDialogVisible.value = true;

  // 提取 knowledge_bases 中每个元素的 id
  const knowledgeBaseIds = item.knowledge_bases.map((kb) => kb.id);
  // 查找匹配的模型对象，使用 available_model_id 进行匹配
  const selectedModel = availableModelStore.llmAvailableModelCfg.find(model => model.id === item.available_model_id);
  
  CreateConversationForm.value = {
    title: item.title,
    model: selectedModel?.id || null,  // 使用 id 而不是 name
    system_prompt: item.system_prompt,
    temperature: item.temperature,
    knowledge_base_ids: knowledgeBaseIds,
    conv_id: item.id,
    use_memory: !!item.use_memory // 同步 use_memory 字段
  } as CreateConversationParams; // 强制类型转换
};

// 提交会话创建/更新
const handleConversationSubmit = async () => {
  try {
    if (!CreateConversationForm.value.model) {
      message.error('请选择模型'); // 提示用户选择模型
      return;
    }

    // 使用对象解构排除 model 字段
    const { model, ...rest } = CreateConversationForm.value;
    const submitForm = {
      ...rest,
      available_model_id: model,  // 直接使用 model 值，因为它已经是 id
      use_memory: CreateConversationForm.value.use_memory ? 1 : 0 // Convert boolean to 1 or 0
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
    system_prompt: '你是我的AI助手',
    temperature: 0.3,
    knowledge_base_ids: [],
    use_memory: true, // 初始化 use_memory 为 true
    conv_id: ""
  };
};

// 会话点击处理
const handleConversationClick = ({ key }: { key: string }) => {
  activeKey.value = [key];
  console.log('Selected:', key); // 添加调试日志
  fetchMessageHistory(key);
};

// 初始化
onMounted(async () => {
  await fetchConversations();
  await fetchKnowledgeList();
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
</style>