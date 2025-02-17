<template>
  <div
    class="source-card"
    :style="{
      transition: open ? 'height 0.4s ease, width 0.4s ease' : 'height 0.4s ease',
      height: open ? '30px' : '200px',
      width: open ? '190px' : '100%',
      background: 'var(--semi-color-tertiary-light-hover)',
      borderRadius: '16px',
      boxSizing: 'border-box',
      marginBottom: '10px',
    }"
  >
    <span
      ref="spanRef"
      class="collapsed-view"
      :style="{
        display: !open ? 'none' : 'flex',
        width: 'fit-content',
        columnGap: '10px',
        background: 'var(--semi-color-tertiary-light-hover)',
        borderRadius: '16px',
        padding: '5px 10px',
        cursor: 'pointer',
        fontSize: '14px',
        color: 'var(--semi-color-text-1)',
      }"
      @click="onOpen"
    >
      <span>基于{{ source.length }}个搜索来源</span>
      <AvatarGroup size="extra-extra-small">
        <Avatar v-for="(s, index) in source" :key="index" :src="s.avatar" />
      </AvatarGroup>
    </span>
    <span
      class="expanded-view"
      :style="{
        height: '100%',
        boxSizing: 'border-box',
        display: !open ? 'flex' : 'none',
        flexDirection: 'column',
        background: 'var(--semi-color-tertiary-light-hover)',
        borderRadius: '16px',
        padding: '12px',
        boxSize: 'border-box',
      }"
      @click="onClose"
    >
      <span
        class="expanded-header"
        :style="{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '5px 10px',
          columnGap: '10px',
          color: 'var(--semi-color-text-1)',
        }"
      >
        <span :style="{ fontSize: '14px', fontWeight: '500' }">参考来源</span>
        <IconChevronUp />
      </span>
      <span
        class="source-list"
        :style="{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '10px',
          overflow: 'scroll',
          padding: '5px 10px',
        }"
      >
        <span
          v-for="s in source"
          :key="s.url"
          class="source-item"
          :style="{
            display: 'flex',
            flexDirection: 'column',
            rowGap: '5px',
            flexBasis: '150px',
            flexGrow: '1',
            border: '1px solid var(--semi-color-border)',
            borderRadius: '12px',
            padding: '12px',
            fontSize: '12px',
          }"
        >
          <span class="source-item-header" :style="{ display: 'flex', columnGap: '5px', alignItems: 'center' }">
            <Avatar :style="{ width: '16px', height: '16px', flexShrink: '0' }" shape="square" :src="s.avatar" />
            <a
              :href="s.url"
              target="_blank"
              class="source-title-link"
              :style="{
                color: 'var(--semi-color-text-2)',
                textOverflow: 'ellipsis',
                textDecoration: 'none', /* Remove underline */
              }"
            >
              <span class="source-title" :style="{ color: 'var(--semi-color-text-2)', textOverflow: 'ellipsis' }">{{ s.title }}</span>

            </a>
          </span>
          <!-- <span class="source-subtitle" :style="{ color: 'var(--semi-color-primary)', fontSize: '12px' }">{{ s.subTitle }}</span> -->
          <!-- <span
            class="source-content"
            :style="{
              display: '-webkit-box',
              WebkitBoxOrient: 'vertical',
              WebkitLineClamp: '3',
              textOverflow: 'ellipsis',
              overflow: 'hidden',
              color: 'var(--semi-color-text-2)',
            }"
          >{{ s.content }}</span> -->
        </span>
      </span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { defineComponent, ref, PropType } from 'vue';
import { Avatar, AvatarGroup } from '@kousum/semi-ui-vue';
import { IconChevronUp } from '@kousum/semi-icons-vue';

defineComponent({ name: 'SourceCard' }); // Optional: Explicitly name the component

interface SourceItem {
  avatar: string;
  url: string;
  title: string;
  content: string;
}

const props = defineProps({
  source: {
    type: Array as PropType<SourceItem[]>,
    required: true,
  },
});

const open = ref(true);
const show = ref(false);
const spanRef = ref(null);

const onOpen = () => {
  open.value = false;
  show.value = true;
};

const onClose = () => {
  open.value = true;
  setTimeout(() => {
    show.value = false;
  }, 350);
};
</script>

<style scoped>
/* You can add scoped styles here if needed, but the component uses mostly inline styles */
.source-card {
  /* Example: If you want to add some global styling that's not inline */
}
.collapsed-view, .expanded-view, .expanded-header, .source-list, .source-item, .source-item-header, .source-title, .source-subtitle, .source-content {
  /* Example: If you want to add some global styling that's not inline */
}
</style>