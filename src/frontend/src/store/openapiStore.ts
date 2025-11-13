import { defineStore } from 'pinia';
import { getOpenApiConfigsList, getOpenApiConfigToolsList } from '@/api/openapi';
import { MessagePlugin } from 'tdesign-vue-next';

interface OpenApiState {
  configs: Api.OpenApiConfigsList | null;
  configDetails: Record<string, Api.OpenApiConfigToolsList>;
  loading: boolean;
  currentPage: number;
  pageSize: number;
}

export const useOpenApiStore = defineStore('openapi', {
  state: (): OpenApiState => ({
    configs: null,
    configDetails: {},
    loading: false,
    currentPage: 1,
    pageSize: 10,
  }),

  actions: {
    // 获取 OpenAPI 配置列表
    async fetchConfigs(page: number = this.currentPage, size: number = this.pageSize) {
      this.loading = true;
      try {
        const response = await getOpenApiConfigsList({ page, size });
        this.configs = response.data;
        this.currentPage = page;
        return response.data;
      } catch (error) {
        MessagePlugin.error('获取OpenAPI配置列表失败');
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 获取特定配置的工具详情
    async fetchConfigTools(configId: string, page: number = 1, size: number = 10) {
      this.loading = true;
      try {
        const response = await getOpenApiConfigToolsList({ config_id: configId, page, size });
        this.configDetails[configId] = response.data.data;
        return response;
      } catch (error) {
        MessagePlugin.error('获取OpenAPI配置工具详情失败');
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 刷新所有数据
    async refreshData() {
      await this.fetchConfigs();
    },
  },
});