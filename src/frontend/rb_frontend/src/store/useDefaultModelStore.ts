// useDefaultModelStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getDefaultCfg } from '@/api/model_cfg';

export const useDefaultModelStore = defineStore('defaultModel', () => {
  const defaultModelCfg = ref(null);
  const isLoading = ref(false);

  const fetchDefaultModelCfg = async () => {
    if (isLoading.value) return;

    isLoading.value = true;
    try {
      const { data } = await getDefaultCfg();
      if (data.status_code === 200) {
        defaultModelCfg.value = data.data;
      } else {
        console.error('获取默认模型配置失败，状态码:', data.status_code);
      }
    } catch (error) {
      console.error('获取默认模型配置时发生网络错误:', error);
    } finally {
      isLoading.value = false;
    }
  };

  return { defaultModelCfg, isLoading, fetchDefaultModelCfg };
});