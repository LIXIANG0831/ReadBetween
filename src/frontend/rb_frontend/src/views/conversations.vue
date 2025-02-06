<template>
  <div class="common-layout">
    <a-layout>
      <a-layout-sider width="256" class="aside">
        <div style="padding: 16px;">
          <a-button type="primary" @click="isCreateDialogVisible = true">
            新建会话
          </a-button>
          <Conversations
            :activeKey="activeKey"
            @activeChange="(key: string) => activeKey = key"
            :items="items"
            :menu="menuConfig"
            :style="style"
          />
          <context-holder />
        </div>
      </a-layout-sider>
      <a-layout>
        <a-layout-content class="main">
          <div style="padding: 16px;">
            <Chat/>


          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>

    <a-modal
      v-model:open="isCreateDialogVisible"
      title="新建会话"
      width="500px"
      @cancel="isCreateDialogVisible = false"
    >
      <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="模型" name="model">
          <a-input v-model:value="form.model" placeholder="请输入模型名称" disabled />
        </a-form-item>
        <a-form-item label="系统提示" name="system_prompt">
          <a-input v-model:value="form.system_prompt" placeholder="请输入系统提示" />
        </a-form-item>
        <a-form-item label="温度" name="temperature">
          <div class="slider-container">
            <a-slider
              v-model:value="form.temperature"
              :min="0.1"
              :max="2"
              :step="0.1"
              :tooltipOpen="true"
              :tooltip-formatter="value => `${value.toFixed(1)}`"
              style="flex: 1; margin-right: 12px;"
            />
            <div class="value-display">
              {{ form.temperature.toFixed(1) }}
            </div>
          </div>
        </a-form-item>
        <a-form-item label="知识库" name="knowledge_base_ids">
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
        <a-button @click="isCreateDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="createNewConversation">创建</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
// 
import { Chat, Radio, RadioGroup } from '@kousum/semi-ui-vue';

import { h } from 'vue';
import { Button, Layout, Modal, Form, Input, Select, message, Slider } from 'ant-design-vue';
import { DeleteOutlined, EditOutlined, StopOutlined } from '@ant-design/icons-vue';
import { Conversations } from 'ant-design-x-vue';
import { computed, ref, onMounted } from 'vue';
import { theme } from 'ant-design-vue';
import type { UploadChangeParam, UploadFile } from 'ant-design-vue';
import { FrownOutlined, SmileOutlined, SyncOutlined, UserOutlined } from '@ant-design/icons-vue';
import { BubbleList } from 'ant-design-x-vue';
import { Flex, Space, Spin } from 'ant-design-vue';
import type { BubbleListProps } from 'ant-design-x-vue';
import { useDefaultModelStore } from '@/store/useDefaultModelStore';

import { 
  createConversation,
  listConversations,
  type Api,
} from '@/api/conversations';
import {
  listKnowledge,
} from '@/api/knowledge';

const defaultModelStore = useDefaultModelStore();
const defaultModelCfg = ref(null);
const AButton = Button;
const ALayout = Layout;
const ALayoutSider = Layout.Sider;
const ALayoutContent = Layout.Content;
const AModal = Modal;
const AForm = Form;
const AFormItem = Form.Item;
const AInput = Input;
const ASelect = Select;
const ASelectOption = Select.Option;
const AInputNumber = Input.Number;
const ASlider = Slider;


const [messageApi, contextHolder] = message.useMessage();

interface ConversationItem {
  key: string;
  label: string;
}

const items = ref<ConversationItem[]>([]);
const activeKey = ref<string | null>(null);
const { token } = theme.useToken();
const isCreateDialogVisible = ref(false);
const form = ref<Api.CreateConversationParams>({
  title: '新会话',
  model: '',
  system_prompt: 'System prompt here',
  temperature: 0.1,
  knowledge_base_ids: [],
});
const knowledgeList = ref<Api.Knowledge[]>([]);

const style = computed(() => ({
  width: '256px',
  background: token.value.colorBgContainer,
  borderRadius: token.value.borderRadius,
}));

const menuConfig = (conversation: ConversationItem) => ({
  items: [
    { label: '修改', key: 'operation1', icon: h(EditOutlined) },
    { label: '删除', key: 'operation3', icon: h(DeleteOutlined), danger: true },
  ],
  onClick: (menuInfo: any) => {
    messageApi.info(`Click ${conversation.key} - ${menuInfo.key}`);
  },
});

const fetchConversations = async () => {
  try {
    const response = await listConversations();
    if (response.data.status_code === 200) {
      items.value = response.data.data.data.map((item: Api.Conversation) => ({
        key: item.conv_id,
        label: item.title || `Conversation ${item.conv_id}`,
      }));
      if (items.value.length > 0) {
        activeKey.value = items.value[0].key;
      }
    }
  } catch (error) {
    messageApi.error('Error fetching conversations');
  }
};

const fetchKnowledgeList = async () => {
  try {
    const response = await listKnowledge();
    if (response.data.status_code === 200) {
      knowledgeList.value = response.data.data.data;
    }
  } catch (error) {
    messageApi.error('Error fetching knowledge list');
  }
};

const createNewConversation = async () => {
  try {
    const params = {
      ...form.value,
      temperature: Number(form.value.temperature),
      knowledge_base_ids: form.value.knowledge_base_ids.map(String)
    };
    
    const response = await createConversation(params);
    if (response.data.status_code === 200) {
      messageApi.success('Conversation created');
      await fetchConversations();
      isCreateDialogVisible.value = false;
    }
  } catch (error) {
    messageApi.error('Error creating conversation');
  }
};

onMounted(() => {
  fetchConversations();
  fetchKnowledgeList();
  // 在组件挂载时加载默认模型配置
  defaultModelStore.loadDefaultModelCfg();
  defaultModelCfg.value = defaultModelStore.defaultModelCfg;
});

// 监听 defaultModelCfg 的变化
watch(defaultModelCfg, (newVal) => {
  if (newVal) {
    form.value.model = newVal.llm_name || '未设置默认模型配置';
  }
}, { immediate: true });
</script>

<style scoped>
.common-layout {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.aside {
  background-color: v-bind('token.colorBgContainer');
  overflow: auto;
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
}
</style>