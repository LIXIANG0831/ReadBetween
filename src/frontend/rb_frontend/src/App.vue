<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  HomeIcon,
  BookIcon,
  TreeRoundDotVerticalIcon,
  ToolsIcon,
  RocketIcon
} from 'tdesign-icons-vue-next'
import { ConfigProvider as TConfigProvider } from 'tdesign-vue-next'
import readbetween from '@/assets/readbetween.svg'

const router = useRouter()
const activeIndex = ref('')

const menuItems = [
  { value: '0', icon: HomeIcon, label: '渠道管理', route: '/conversations' },
  { value: '1', icon: BookIcon, label: '知识库管理', route: '/knowledge' },
  { value: '2', icon: TreeRoundDotVerticalIcon, label: '记忆管理', route: '/memory' },
  { value: '3', icon: ToolsIcon, label: 'MCP管理', route: '/mcp' },
  { value: '4', icon: RocketIcon, label: '模型管理', route: '/model_cfg' },
]

const handleSelect = (value: string) => {
  activeIndex.value = value
  const selectedItem = menuItems.find(item => item.value === value)
  if (selectedItem) {
    router.push(selectedItem.route)
  }
}
</script>

<template>
  <TConfigProvider :theme="{ primaryColor: '#3875F6' }">
    <t-layout class="app-container">
      <!-- 顶栏 -->
      <t-header class="app-header">
        <div class="header-content">
          <div class="logo-section">
            <!-- <h2>ReadBetween</h2> -->
            <img height="28" :src="readbetween" alt="logo" />
          </div>
          <div class="menu-container">
            <t-head-menu
            v-model="activeIndex"
            theme="light"
            mode="horizontal"
            @change="handleSelect"
            class="header-menu"
            >
              <t-menu-item 
                v-for="item in menuItems"
                :key="item.value"
                :value="item.value"
              >
                <template #icon>
                  <component :is="item.icon" />
                </template>
                {{ item.label }}
              </t-menu-item>
            </t-head-menu>
          </div>
        </div>
      </t-header>

      <!-- 主内容区 -->
      <t-content class="app-content">
        <router-view />
      </t-content>
    </t-layout>
  </TConfigProvider>
</template>

<style lang="scss" scoped>
// 全局变量定义
:root {
  --header-height: 64px;
  --primary-color: #3875F6;  
  --primary-light-color: #EBF1FF; 
  --text-primary: #1d2129;
  --text-secondary: #4e5969;
  --border-color: #e5e6eb;
  --bg-color: #f7f8fa;
  --white: #ffffff;
}

// 基础布局
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
}

// 顶栏样式
.app-header {
  height: var(--header-height);
  background: var(--white);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
  border-bottom: 1px solid var(--border-color);

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;

    .menu-container {
      margin: 0 auto; // 水平居中关键代码
    }
  }

  .logo-section h2 {
    font-size: 22px;
    font-weight: 600;
    color: var(--primary-color);
    margin: 0;
  }
}

// 菜单样式
.header-menu {
  background: transparent;
  border: none;
  height: 100%;

  :deep(.t-menu__item) {
    color: var(--text-primary);
    border-radius: 6px;
    margin: 0 8px;
    transition: all 0.2s ease;
    height: 40px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-size: 16px;

    &:hover {
      background-color: var(--primary-light-color);
    }

    &.t-is-active {
      background-color: var(--primary-light-color);
      color: var(--primary-color);
      font-weight: 500;
      
      .t-icon {
        color: var(--primary-color);
      }
    }

    .t-icon {
      font-size: 18px;
      margin-right: 8px;
      color: var(--text-secondary);
    }
  }
}

// 主内容区
.app-content {
  flex: 1;
  padding: 20px;
  background-color: var(--white);
  overflow-y: auto;
  height: calc(100vh - var(--header-height) - 40px);
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

#app {
  height: 100vh;
  color: #1d2129;
}
</style>