<script setup lang="ts">
import { ConfigProvider as TConfigProvider } from 'tdesign-vue-next'
import TopMenu from '@/components/TopMenu.vue'
</script>

<template>
  <TConfigProvider :theme="{ primaryColor: '#3875F6' }">
    <t-layout class="app-container">

      <!-- 顶栏 -->
      <t-header class="app-header">
        <TopMenu />
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
