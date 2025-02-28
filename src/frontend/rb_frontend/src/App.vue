<script setup lang="ts">
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { FolderOpenOutlined, HomeOutlined, BookOutlined, RocketOutlined, DeploymentUnitOutlined } from '@ant-design/icons-vue';
import { XProvider } from 'ant-design-x-vue';

const locale = zhCN;
const router = useRouter();
const activeIndex = ref('0');

const handleSelect = (event: { key: string }) => {
  const key = event.key;
  if (key === '0') {
    router.push('/');
  } else if (key === '1') {
    router.push('/knowledge');
  }
  else if (key === '2') {
    router.push('/memory');
  }
  else if (key === '3') {
    router.push('/model_cfg');
  }
};
</script>

<template>
  <XProvider :locale="locale">
    <a-layout style="height: 100vh; overflow: hidden;">
      <a-layout-sider 
        width="200" 
        theme="light"
        class="ant-layout-sider-custom"
      >
        <a-menu
          mode="inline"
          :default-selected-keys="[activeIndex]"
          @click="handleSelect"
          class="menu-container"
        >
          <a-menu-item key="0">
            <template #icon>
              <HomeOutlined />
            </template>
            <span>🏠 渠道</span>
          </a-menu-item>
          
          <a-menu-item key="1">
            <template #icon>
              <BookOutlined />
            </template>
            <span>📚 知识库管理</span>
          </a-menu-item>

          <a-menu-item key="2">
            <template #icon>
              <DeploymentUnitOutlined />
            </template>
            <span>🧠 记忆管理</span>
          </a-menu-item>

          <a-menu-item key="3">
            <template #icon>
              <RocketOutlined />
            </template>
            <span>🚀 模型管理</span>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>

      <a-layout>
        <a-layout-content class="content-wrapper">
          <router-view />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </XProvider>
</template>

<style scoped>
/* 移除默认边距 */
:deep(.ant-layout) {
  margin: 0;
  padding: 0;
}

.ant-layout-sider-custom {
  background: #fff;
  border-right: 1px solid #e8e8e8;
  height: 100vh;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1); /* 添加阴影 */
  border-radius: 0 8px 8px 0; /* 添加圆角 */
}

.menu-container {
  border-right: 0;
  height: calc(100vh - 16px); /* 留出滚动条空间 */
  padding: 8px 0;
}

.content-wrapper {
  padding: 20px;
  height: 100vh;
  overflow-y: auto;
  background: #f0f2f5;
  border-radius: 8px; /* 添加圆角 */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); /* 添加阴影 */
}
</style>

<style>
/* 全局样式重置 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}

#app {
  height: 100vh;
}

/* 调整菜单项样式 */
.ant-menu-item {
  margin: 4px 8px !important;
  border-radius: 4px;
  transition: background-color 0.3s ease; /* 添加过渡效果 */
}

.ant-menu-item-selected {
  background-color: #e6f7ff !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); /* 添加选中状态阴影 */
}
</style>