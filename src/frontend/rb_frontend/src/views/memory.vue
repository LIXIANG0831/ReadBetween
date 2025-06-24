<template>
  <div class="common-layout">
    <t-layout style="height: 100vh;">
      <t-aside width="250px" class="aside">
        <div style="padding: 16px; height: 100%; display: flex; flex-direction: column;">
          <div style="margin-bottom: 16px; color: var(--td-text-color-secondary);">
            <span>渠道记忆</span>
            <p style="font-size: 12px; margin-top: 4px;">点击渠道查看记忆图谱。</p>
          </div>

          <t-menu
            v-model="activeKey"
            theme="light"
            style="flex: 1;"
            @change="handleConversationClick"
          >
            <t-menu-item 
              v-for="item in filteredItems" 
              :key="item.id" 
              :value="item.id"
              class="menu-item"
            >
              <template #icon>
                <t-icon name="chat" />
              </template>
              {{ item.title || `会话 ${item.id}` }}
            </t-menu-item>
          </t-menu>
        </div>
      </t-aside>
      <t-layout>
        <t-content class="main">
          <div v-if="activeKey" class="graph-container">
            <KnowledgeGraph :user-id="activeKey"></KnowledgeGraph>
          </div>
          <div v-else class="read-between-placeholder">
            ReadBetween
          </div>
        </t-content>
      </t-layout>
    </t-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  MessagePlugin,
} from 'tdesign-vue-next';
import {
  listConversations,
} from '@/api/conversation';
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import KnowledgeGraph from '@/components/KnowledgeGraph.vue';

const availableModelStore = useAvailableModelStore();

// 状态管理
const activeKey = ref<string>('');
const items = ref<Api.Conversation[]>([]);

// 获取会话列表
const fetchConversations = async () => {
  try {
    const res = await listConversations();
    if (res.data.status_code === 200) {
      items.value = res.data.data.data;
    }
  } catch (error) {
    MessagePlugin.error('获取会话列表失败');
  }
};

// 会话点击处理
const handleConversationClick = (key: string) => {
  activeKey.value = key;
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
  background-color: var(--td-bg-color-container);
  overflow: auto;
  height: 100%;
  border-right: 1px solid var(--td-component-stroke);
}

.main {
  background-color: var(--td-bg-color-container);
  padding: 24px;
  flex: 1;
  overflow: auto;
  height: 100%;
}

.menu-item {
  position: relative;
}

.read-between-placeholder {
  font-size: 96px;
  color: var(--td-text-color-placeholder);
  text-align: center;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 300;
  opacity: 0.6;
}

.graph-container {
  width: 100%;
  height: 100%;
  background: var(--td-bg-color-page);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 16px;
}

/* Add smooth transitions for better UX */
.t-menu {
  transition: all 0.3s ease;
}

.t-menu-item {
  transition: background-color 0.2s ease;
}
</style>