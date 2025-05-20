import { defineStore } from 'pinia'
import { getAvailableModelCfgList } from '@/api/model_cfg';

interface ModelConfig {
  id: string;
  name: string;
  type: string;
  // 添加其他必要的字段
}

interface AvailableModelState {
  allAvailableModelCfg: ModelConfig[] | null;
  llmAvailableModelCfg: ModelConfig[];
  embeddingAvailableModelCfg: ModelConfig[];
  isLoading: boolean;
}

export const useAvailableModelStore = defineStore('available_model', {
  state: (): AvailableModelState => ({
    allAvailableModelCfg: null, // 所有模型配置
    llmAvailableModelCfg: [], // LLM 类型的模型配置
    embeddingAvailableModelCfg: [], // Embedding 类型的模型配置
    isLoading: true, // 加载状态标志
  }),
  actions: {
    async loadAvailableModelCfg() {
      this.isLoading = true; // 开始加载
      try {
        const { data } = await getAvailableModelCfgList();
        if (data.status_code === 200) {
          this.allAvailableModelCfg = data.data; // 设置所有模型配置

          // 根据类型分类模型配置
          this.llmAvailableModelCfg = data.data.filter((model) => model.type === 'llm');
          this.embeddingAvailableModelCfg = data.data.filter((model) => model.type === 'embedding');
        } else {
          console.error(data.status_message || '获取可用模型失败');
        }
      } catch (error) {
        console.error('获取可用模型失败:', error);
      } finally {
        this.isLoading = false; // 加载完成
      }
    },
    setAvailableModelCfg(cfg: ModelConfig[]) {
      this.allAvailableModelCfg = cfg; // 更新所有模型配置
      // 同时更新分类后的模型配置
      this.llmAvailableModelCfg = cfg.filter((model) => model.type === 'llm');
      this.embeddingAvailableModelCfg = cfg.filter((model) => model.type === 'embedding');
    },
  },
  persist: true, // 开启持久化存储，可选
});