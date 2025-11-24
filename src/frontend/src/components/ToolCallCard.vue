<template>
  <div class="tool-card-wrapper">
    <div class="tool-card" :class="{ expanded: isExpanded }">
      <!-- 头部 -->
      <div class="card-header" @click="toggleExpand">
        <div class="header-content">
          <div class="icon-container">
            <icon name="tools" />
          </div>
          <div class="text-content">
            <div class="title">{{ toolCall.function.name }}</div>
            <div class="subtitle" v-if="!isExpanded">{{ briefContent }}</div>
          </div>
        </div>
        <t-button variant="text" size="small" @click.stop="toggleExpand">
          {{ isExpanded ? '收起' : '展开' }}
          <icon :name="isExpanded ? 'chevron-up' : 'chevron-down'" />
        </t-button>
      </div>

      <!-- 内容区域 -->
      <t-collapse-transition>
        <div v-show="isExpanded" class="card-body">
          <div class="section">
            <div class="section-title">
              <icon name="code" />
              <span>调用参数</span>
            </div>
            <pre class="code-block">{{ formattedArguments }}</pre>
          </div>
          
          <div class="section">
            <div class="section-title">
              <icon name="server" />
              <span>返回结果</span>
            </div>
            <pre class="code-block">{{ formattedContent }}</pre>
          </div>
        </div>
      </t-collapse-transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Icon } from 'tdesign-icons-vue-next'

const props = defineProps({
  toolCall: Object,
  content: String
})

const isExpanded = ref(false)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const formattedArguments = computed(() => {
  try {
    return JSON.stringify(JSON.parse(props.toolCall.function.arguments), null, 2)
  } catch {
    return props.toolCall.function.arguments
  }
})

const formattedContent = computed(() => {
  try {
    return JSON.stringify(JSON.parse(props.content), null, 2)
  } catch {
    return props.content
  }
})

const briefContent = computed(() => {
  const args = props.toolCall.function.arguments
  try {
    const parsed = JSON.parse(args)
    return Object.values(parsed).slice(0, 2).join(", ")
  } catch {
    return args.length > 30 ? args.substring(0, 30) + "..." : args
  }
})
</script>

<style scoped lang="less">
.tool-card-wrapper {
  margin: 12px 0;
  width: 100%; /* 默认100%宽度 */
  max-width: 1000px; /* 设置最大宽度 */
  min-width: 600px; /* 设置最小宽度 */
}


.tool-card {
  background: var(--td-bg-color-container);
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  border: 1px solid transparent; // 添加透明边框保持布局稳定
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
    border-color: var(--td-brand-color); // 使用品牌色作为蓝色边框
  }
  
  &.expanded {
    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
  }
}


.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: var(--td-bg-color-container-hover);
  }
  
  .header-content {
    display: flex;
    align-items: center;
    flex: 1;
    min-width: 0;
    gap: 12px;
  }
  
  .icon-container {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: var(--td-brand-color-1);
    display: flex;
    align-items: center;
    justify-content: center;
    
    .t-icon {
      color: var(--td-brand-color);
    }
  }
  
  .text-content {
    flex: 1;
    min-width: 0;
    
    .title {
      font-weight: 500;
      font-size: 14px;
      color: var(--td-text-color-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .subtitle {
      font-size: 12px;
      color: var(--td-text-color-placeholder);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.card-body {
  padding: 0 16px 16px;
  border-top: 1px solid var(--td-component-stroke);
}

.section {
  margin-top: 16px;
  
  &:first-child {
    margin-top: 0;
  }
  
  &-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
    color: var(--td-text-color-secondary);
    margin-bottom: 8px;
    
    .t-icon {
      color: var(--td-brand-color);
    }
  }
}

.code-block {
  background: var(--td-bg-color-secondarycontainer);
  border-radius: 4px;
  padding: 12px;
  margin: 0;
  font-family: var(--td-font-family-mono);
  font-size: 13px;
  line-height: 1.5;
  color: var(--td-text-color-primary);
  white-space: pre-wrap;
  overflow-x: auto;
  border: 1px solid var(--td-component-stroke);
}
</style>