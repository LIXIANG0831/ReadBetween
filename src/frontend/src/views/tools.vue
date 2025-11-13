<template>
  <div class="tools-container">
    <t-tabs v-model:value="activeTab" class="tools-tabs" @change="handleTabChange">
      <t-tab-panel value="mcp" label="MCP配置管理">
        <mcp-management />
      </t-tab-panel>
      <t-tab-panel value="openapi" label="OpenAPI配置管理">
        <open-api-management />
      </t-tab-panel>
    </t-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import McpManagement from './mcp.vue';
import OpenApiManagement from './openapi.vue';

const activeTab = ref('mcp');

const handleTabChange = (value: string) => {
  activeTab.value = value;
};
</script>

<style scoped>
.tools-container {
  padding: 20px;
  background-color: var(--td-bg-color-container);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tools-tabs {
  :deep(.t-tabs__header) {
    background-color: var(--td-bg-color-container);
    border-bottom: 1px solid var(--td-border-level-1-color);
    padding: 0 20px;
    margin-bottom: 20px;
  }

  :deep(.t-tabs__nav-item) {
    font-size: 16px;
    font-weight: 500;
    padding: 12px 24px;
    position: relative;
    
    &.t-is-active {
      color: var(--td-brand-color);
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background-color: var(--td-brand-color);
        border-radius: 2px;
      }
    }
  }
}
</style>