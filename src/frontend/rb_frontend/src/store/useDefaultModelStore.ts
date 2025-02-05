// stores/useDefaultModelStore.ts
import { defineStore } from 'pinia';
import { getDefaultCfg } from '@/api/model_cfg';

export const useDefaultModelStore = defineStore('defaultModelStore', {
  state: () => ({
    defaultModelCfg: null, // 默认模型配置，初始值为 null
    isLoading: true, // 加载状态标志
  }),
  actions: {
    async loadDefaultModelCfg() {
      this.isLoading = true; // 开始加载
      try {
        const { data } = await getDefaultCfg();
        if (data.status_code === 200) {
          this.defaultModelCfg = data.data; // 设置默认模型配置
        } else {
          console.error(data.status_message || '获取默认配置失败');
        }
      } catch (error) {
        console.error('获取默认模型配置失败:', error);
      } finally {
        this.isLoading = false; // 加载完成
      }
    },
    setDefaultModelCfg(cfg) {
      this.defaultModelCfg = cfg; // 更新默认模型配置
    },
  },
  persist: true, // 开启持久化存储，可选
});