<template>
  <t-card v-if="sources && sources.length > 0" class="source-card" :bordered="false">
    <template #header>
      <div class="source-header" @click="toggleCollapse">
        <Filter3Icon />
        <span class="header-text">信息来源</span>
        <component :is="collapsed ? ChevronRightIcon : ChevronDownIcon" class="collapse-icon" />
      </div>
    </template>
    <div class="source-list-wrapper" v-show="!collapsed">
      <div class="source-list">
        <t-tooltip v-for="(source, index) in processedSources" :key="index" :content="source.title || source.url" placement="top">
          <a :href="source.url" target="_blank" rel="noopener noreferrer" class="source-item">
            <div class="source-avatar">
              <img v-if="source.avatar" :src="source.avatar" :alt="source.title" class="favicon" @error="handleImageError">
              <div v-else class="default-avatar">
                {{ getInitials(source.title || source.url) }}
              </div>
            </div>
            <div class="source-content">
              <div class="source-title" v-if="source.title">{{ truncate(source.title, 20) }}</div>
              <div class="source-domain">{{ extractDomain(source.url) }}</div>
            </div>
          </a>
        </t-tooltip>
      </div>
    </div>
  </t-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Filter3Icon, ChevronRightIcon, ChevronDownIcon } from 'tdesign-icons-vue-next';
import { Card as TCard, Tooltip as TTooltip } from 'tdesign-vue-next';
import KbIcon from '@/assets/kb.svg';

interface Source {
  url: string;
  title?: string;
  source?: string;
  avatar?: string;
}

const props = defineProps({
  sources: {
    type: Array as () => Source[],
    default: () => []
  },
  defaultCollapsed: {
    type: Boolean,
    default: true
  }
});

const collapsed = ref(props.defaultCollapsed);

const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
};

const processedSources = computed(() => {
  return props.sources.map((item: Source) => {
    try {
      if (item.source === 'kb') {
        return { 
          ...item, 
          avatar: KbIcon
        };
      } else if (item.source === 'web') {
        const urlObj = new URL(item.url);
        const faviconUrl = `${urlObj.origin}/favicon.ico`;
        return { 
          ...item, 
          avatar: faviconUrl
        };
      }
      return item;
    } catch {
      return item;
    }
  });
});

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.style.display = 'none';
  const parent = target.parentElement;
  if (parent) {
    const defaultAvatar = parent.querySelector('.default-avatar') as HTMLElement;
    if (defaultAvatar) {
      defaultAvatar.style.display = 'flex';
    }
  }
};

const getInitials = (text: string) => {
  if (!text) return '?';
  const words = text.split(' ');
  if (words.length === 1) return text.charAt(0).toUpperCase();
  return words[0].charAt(0).toUpperCase() + words[1].charAt(0).toUpperCase();
};

const truncate = (text: string, length: number) => {
  if (!text) return '';
  return text.length > length ? text.substring(0, length) + '...' : text;
};

const extractDomain = (url: string) => {
  if (!url) return '';
  try {
    const domain = new URL(url).hostname.replace('www.', '');
    return domain.length > 15 ? domain.substring(0, 15) + '...' : domain;
  } catch {
    return url.length > 15 ? url.substring(0, 15) + '...' : url;
  }
};
</script>

<style scoped lang="less">
.source-card {
  margin: 12px 0;
  background-color: var(--td-bg-color-container);
  
  :deep(.t-card__header) {
    padding: 8px 12px;
    border-bottom: none;
  }
}

.source-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  color: var(--td-text-color-secondary);
  
  .t-icon {
    font-size: 16px;
  }
  
  .header-text {
    margin: 0 8px;
    font-size: 20px;
    flex-grow: 1;
  }
  
  .collapse-icon {
    transition: transform 0.2s;
  }
  
  &:hover {
    color: var(--td-text-color-primary);
  }
}

.source-list-wrapper {
  overflow-x: auto;
  padding: 0 8px 8px;
  
  &::-webkit-scrollbar {
    height: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: var(--td-scrollbar-color);
    border-radius: 2px;
  }
}

.source-list {
  display: inline-flex;
  gap: 8px;
  padding: 0;
  min-width: 100%;
}

.source-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 12px; /* 增大圆角 */
  background-color: white;
  text-decoration: none;
  color: inherit;
  min-width: 160px;
  max-width: 200px;
  box-sizing: border-box;
  transition: all 0.2s;
  border: 1px solid var(--td-component-stroke);
  
  &:hover {
    border-color: var(--td-brand-color);
    background-color: var(--td-bg-color-container-hover);
  }
}

.source-avatar {
  width: 24px;
  height: 24px;
  border-radius: 8px; /* 增大圆角 */
  background-color: var(--td-bg-color-component);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  flex-shrink: 0;
}

.favicon {
  width: 14px;
  height: 14px;
  object-fit: contain;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: none;
  align-items: center;
  justify-content: center;
  background-color: var(--td-brand-color);
  color: white;
  font-size: 11px;
  font-weight: bold;
  border-radius: 8px; /* 增大圆角 */
}

.source-content {
  flex: 1;
  min-width: 0;
}

.source-title {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--td-text-color-primary);
}

.source-domain {
  font-size: 11px;
  color: var(--td-text-color-placeholder);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>