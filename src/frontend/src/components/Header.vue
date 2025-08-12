<script setup lang="ts">
import { isDark, toggleDark } from '@/utils/dark';
import { useDialogStore } from '@/store/dialog';

const { t, availableLocales, locale } = useI18n();
const dialogStore = useDialogStore();

const toggleLocales = () => {
  const locales = availableLocales;
  locale.value = locales[(locales.indexOf(locale.value) + 1) % locales.length];
};
</script>

<template>
  <div class="horizontal-header">
    <div class="spacer" />
    <!-- 空白元素，用于推动按钮到右侧 -->
    <el-tooltip :content="isDark ? t('change light') : t('change dark')" placement="top">
      <el-button class="icon-btn mx-2 !outline-none" @click="toggleDark()">
        <i-ph-cloud-moon-bold v-if="isDark" />
        <i-ph-sun-horizon-bold v-else />
      </el-button>
    </el-tooltip>
    <el-tooltip :content="t('change lang')" placement="top">
      <el-button class="icon-btn mx-2" @click="toggleLocales()">
        <i-la-language />
      </el-button>
    </el-tooltip>
    <el-tooltip :content="t('change lang')" placement="top">
      <el-button @click="dialogStore.openLoginDialog">{{ t('header.login') }}</el-button>
    </el-tooltip>
  </div>
</template>

<style lang="scss" scoped>
.horizontal-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.spacer {
  flex: 1; /* 自动填充剩余空间 */
}
</style>
