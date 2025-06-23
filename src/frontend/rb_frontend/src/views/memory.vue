<template>
  <div class="common-layout">
    <a-layout style="height: 100vh;">
      <a-layout-sider width="250px" class="aside" style="height: 100%;margin-bottom: 16px;">
        <div style="padding: 16px;height: 100%;display: flex;flex-direction: column;">

          <div style="margin-bottom: 16px; color: var(--semi-color-text-2);">
            <span>渠道记忆</span>
            <p style="font-size: 12px; margin-top: 4px;">点击渠道查看记忆图谱。</p>
          </div>

          <a-menu
            v-model:selectedKeys="activeKey"
            mode="inline"
            :style="style"
            @click="handleConversationClick"
          >
            <a-menu-item v-for="item in filteredItems" :key="item.id" class="menu-item">
              <template #icon>
                <message-outlined />
              </template>
              <span>{{ item.title || `会话 ${item.id}` }}</span>
            </a-menu-item>
          </a-menu>
        </div>
      </a-layout-sider>
      <a-layout>
        <a-layout-content class="main">
          <div v-if="activeKey.length > 0" style="width: 100%;">
            <KnowledgeGraph :user-id="activeKey[0]"></KnowledgeGraph>
          </div>
          <div v-else class="read-between-placeholder">
            ReadBetween
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  message,
  Menu as AMenu,
} from 'ant-design-vue';
import {
  MessageOutlined
} from '@ant-design/icons-vue';
import { theme } from 'ant-design-vue';
import {
  listConversations,
} from '@/api/conversation';
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import KnowledgeGraph from '@/components/KnowledgeGraph.vue'; // 引入 KnowledgeGraph 组件


const availableModelStore = useAvailableModelStore();
const { token } = theme.useToken();

// 状态管理
const activeKey = ref<string[]>([]);
const items = ref<Api.Conversation[]>([]);

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
    }
  } catch (error) {
    message.error('获取会话列表失败');
  }
};

// 会话点击处理
const handleConversationClick = ({ key }: { key: string }) => {
  activeKey.value = [key];
};

// 初始化
onMounted(async () => {
  await fetchConversations();
  availableModelStore.loadAvailableModelCfg();
});

// 筛选 use_memory 为 1 的会话
const filteredItems = computed(() => {
  return items.value.filter(item => item.use_memory === 1);
});
</script>

<style scoped>
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