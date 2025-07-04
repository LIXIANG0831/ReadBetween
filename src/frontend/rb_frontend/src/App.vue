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
      <!-- 侧边栏 -->
      <t-aside class="app-sidebar">
        <div class="sidebar-header">
          <h2>ReadBetween</h2>
        </div>
        
        <t-menu
          v-model="activeIndex"
          theme="light"
          @change="handleSelect"
          class="sidebar-menu"
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
        </t-menu>
      </t-aside>

      <!-- 主内容区 -->
      <t-layout>
        <t-content class="app-content">
          <router-view />
        </t-content>
      </t-layout>
    </t-layout>
  </TConfigProvider>
</template>

<style lang="scss" scoped>
// 全局变量定义
:root {
  --sidebar-width: 280px;
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
  background-color: var(--bg-color);
}

// 侧边栏样式
.app-sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--white);
  box-shadow: 1px 0 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 100;
  border-right: 1px solid var(--border-color);
  transition: width 0.2s ease;

  .sidebar-header {
    padding: 20px;
    color: var(--primary-color);
    text-align: center;
    
    h2 {
      margin-top: 20px;
      font-size: 22px;
      font-weight: 600;
      letter-spacing: 0.5px;
      color: var(--primary-color);
    }
  }
}

// 菜单样式
.sidebar-menu {
  flex: 1;
  background: transparent;
  border-right: none;
  padding: 8px 12px;
  width: 100%;

  :deep(.t-menu__item) {
    color: var(--text-primary);
    border-radius: 6px;
    margin: 16px 0;
    transition: all 0.2s ease;
    height: 50px;
    display: flex;
    align-items: center;
    width: 100%;
    box-sizing: border-box;
    padding: 0 12px;
    font-size: 18px;

    &:hover {
      background-color: var(--primary-light-color);
    }

    &.t-is-active {
      background-color: var(--primary-light-color);
      color: var(--primary-color);
      position: relative;
      font-weight: 500;
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background-color: var(--primary-color);
        border-radius: 0 3px 3px 0;
      }
      
      .t-icon {
        color: var(--primary-color);
      }
      
      transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }

    .t-icon {
      font-size: 18px;
      margin-right: 10px;
      color: var(--text-secondary);
    }
  }
}

// 主内容区
.app-content {
  padding: 20px;
  background-color: var(--white);
  height: calc(100vh - 40px);
  overflow-y: auto;
  border-radius: 8px 0 0 0;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.03);
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