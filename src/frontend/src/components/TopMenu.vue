<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BookIcon,
  HomeIcon,
  RocketIcon,
  ToolsIcon,
  TreeRoundDotVerticalIcon
} from 'tdesign-icons-vue-next'
import readbetween from '@/assets/readbetween.svg'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { value: '/conversations', icon: HomeIcon, label: '渠道管理' },
  { value: '/knowledge', icon: BookIcon, label: '知识库管理' },
  { value: '/memory', icon: TreeRoundDotVerticalIcon, label: '记忆管理' },
  { value: '/mcp', icon: ToolsIcon, label: 'MCP管理' },
  { value: '/model_cfg', icon: RocketIcon, label: '模型管理' }
]

const activeValue = computed(() => {
  const currentPath = route.path
  // Find the menu item that matches the current route.
  // This handles cases where the route is a sub-route of a menu item.
  // For example, if current route is /knowledge/123, the /knowledge menu should be active.
  const activeItem = menuItems
    .slice()
    .reverse()
    .find(item => currentPath.startsWith(item.value))
  return activeItem ? activeItem.value : ''
})

const handleSelect = (value: string) => {
  if (value) {
    router.push(value)
  }
}
</script>

<template>
  <div class="header-content">
    <div>
      <img height="28" :src="readbetween" alt="logo" />
    </div>
    <div class="menu-container">
      <t-head-menu
        :model-value="activeValue"
        class="header-menu"
        mode="horizontal"
        theme="light"
        @change="handleSelect"
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
</template>

<style lang="scss" scoped>
.menu-container {
  margin: 0 auto; // 水平居中关键代码
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

// 菜单样式
.header-menu {
  background: transparent;
  border: none;
  height: 100%;

  :deep(.t-menu__item) {
    color: var(--td-text-color-primary);
    border-radius: 50px;
    margin: 0 8px;
    transition:
      color 0.2s ease,
      background-color 0.2s ease;
    height: 40px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-size: 16px;

    &:hover {
      background-color: var(--td-brand-color-light);
      color: var(--td-brand-color);
      .t-icon {
        color: var(--td-brand-color);
      }
    }

    &.t-is-active {
      background-color: var(--td-brand-color);
      color: #ffffff;
      font-weight: 500;

      .t-icon {
        color: #ffffff;
      }
    }

    .t-icon {
      font-size: 18px;
      margin-right: 1px;
      color: var(--td-text-color-secondary);
      transition: color 0.2s ease;
    }
  }
}
</style>

