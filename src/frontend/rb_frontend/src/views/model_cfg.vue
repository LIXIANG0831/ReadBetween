<template>
  <div class="model-cfg-container">
    <div class="providers-container">
      <a-card 
        v-for="provider in providers" 
        :key="provider.id" 
        size="small"
        class="provider-card"
      >
        <h4>
          <span v-if="provider.mark === 'openai'">🤖</span>
          <span v-else-if="provider.mark === 'openai-compatible'">☁️</span>
          <span v-else-if="provider.mark === 'qwen'">🌐</span>
          <span v-else-if="provider.mark === 'hosted_vllm'">🦔</span>
          {{ provider.provider }}
        </h4>
        <a-button type="primary" @click="handleAddModel(provider)" class="action-btn">
          🛠️ 添加配置
        </a-button>
      </a-card>
    </div>

    <!-- 默认模型展示区域 -->
    <a-card v-if="groupedDefaultModelCfg" class="default-model-card">
      <h3>📌 可用模型配置</h3>

      <a-collapse>
        <!-- 大语言模型区域 -->
        <a-collapse-panel header="💬 大语言模型" key="1">
          <div v-if="groupedDefaultModelCfg.llm.length > 0" class="model-type-section">
            <a-card
              v-for="model in groupedDefaultModelCfg.llm"
              :key="model.id"
              class="available-model-card"
              size="small"
            >
              <template #title>
                <div class="model-card-title">
                  {{ model.name }}
                  <a-popconfirm
                    title="删除该大语言模型，会同步删除已创建的会话渠道，是否确认删除？"
                    @confirm="handleDeleteAvailableModel(model)"
                  >
                    <a-button type="link" danger class="action-button">
                      <template #icon><DeleteOutlined /></template>
                      删除
                    </a-button>
                  </a-popconfirm>
                </div>
              </template>
              <p><strong>🏢 供应商:</strong> {{ getProviderName(model.mark) }}</p>
              <p><strong>🔑 API Key:</strong> {{ model.api_key }}</p>
              <p><strong>🌍 Base URL:</strong> {{ model.base_url }}</p>
            </a-card>
          </div>
          <div v-else class="model-type-section">
            <p>暂无可用大语言模型。</p>
          </div>
        </a-collapse-panel>

        <!-- 向量模型区域 -->
        <a-collapse-panel header="🧬 向量模型【暂不生效使用系统内置向量模型】" key="2">
          <div v-if="groupedDefaultModelCfg.embedding.length > 0" class="model-type-section">
            <a-card
              v-for="model in groupedDefaultModelCfg.embedding"
              :key="model.id"
              class="available-model-card"
              size="small"
            >
              <template #title>
                <div class="model-card-title">
                  {{ model.name }}
                  <a-popconfirm
                    title="删除该向量模型，会同步删除已创建的知识库，是否确认删除？"
                    @confirm="handleDeleteAvailableModel(model)"
                  >
                    <a-button type="link" danger class="action-button">
                      <template #icon><DeleteOutlined /></template>
                      删除
                    </a-button>
                  </a-popconfirm>
                </div>
              </template>
              <p><strong>🏢 供应商:</strong> {{ getProviderName(model.mark) }}</p>
              <p><strong>🔑 API Key:</strong> {{ model.api_key }}</p>
              <p><strong>🌍 Base URL:</strong> {{ model.base_url }}</p>
            </a-card>
          </div>
          <div v-else class="model-type-section">
            <p>暂无可用向量模型。</p>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </a-card>
    <a-card v-else class="default-model-card">
      <h3>📌 可用模型配置</h3>
      <p>暂无可用模型配置。</p>
    </a-card>

    <div class="models-container">
      <a-table 
        :dataSource="models" 
        :columns="modelColumns" 
        rowKey="id"
        :pagination="{ pageSize: 6 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-button type="link" @click="handleSetDefault(record)" class="action-link">
              ⭐ 添加模型
            </a-button>
            <a-button type="link" @click="handleDeleteModel(record)" class="action-link">
              🗑️ 删除
            </a-button>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 添加配置弹窗 -->
    <a-modal
      v-model:open="addDialogVisible"
      title="➕ 添加模型配置"
      centered
      :destroyOnClose="true"
      @cancel="addDialogVisible = false"
    >
      <a-form :model="addForm" :label-col="{ span: 4 }">
        <a-form-item label="🏢供应商">
          <a-input v-model:value="addForm.name" disabled />
        </a-form-item>
        <a-form-item label="🔑API密钥" required>
          <a-input v-model:value="addForm.api_key" />
        </a-form-item>
        <a-form-item label="🌍BaseUrl" required>
          <a-input v-model:value="addForm.base_url" />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="addDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="saveAddModel">保存</a-button>
      </template>
    </a-modal>

    <!-- 设置默认弹窗 -->
    <a-modal
      v-model:open="setDefaultDialogVisible"
      title="⭐ 添加可用模型"
      centered
      :destroyOnClose="true"
      @cancel="setDefaultDialogVisible = false"
    >
      <a-form :model="setDefaultForm" :label-col="{ span: 4 }">
        <a-form-item label="模型类型" required>  <!-- 修改 Label 为 "模型类型" -->
          <a-select
            v-model:value="setDefaultForm.modelType" 
            placeholder="请选择模型类型"
            :options="[  //  模型类型选项
              { label: '🧬 向量模型', value: 'embedding' },
              { label: '💬 大语言模型', value: 'llm' },
            ]"
          />
        </a-form-item>

        <a-form-item label="选择模型" required>  <!-- 修改 Label 为 "选择模型" -->
          <a-select
            v-model:value="setDefaultForm.selectedModelName"
            placeholder="请选择模型"
            :options="availableModels"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="setDefaultDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="addAvailableModel">添加</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { 
  listProviders, 
  createModelCfg, 
  deleteModelCfg, 
  listModelCfg, 
  getAvailableModelCfg,
  getAvailableModelCfgList,
  addAvailableModelCfg,
  deleteAvailableModelCfg,
} from '@/api/model_cfg';
import { useAvailableModelStore } from '@/store/useAvailableModelStore';

import {
  CheckOutlined,
  CloseOutlined,
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'

interface Provider {
  id: string;
  provider: string;
  mark: string;
}

interface ModelCfg {
  id: string;
  provider_id: string;
  name: string;
  api_key: string;
  base_url: string;
  embedding_name?: string;
  llm_name?: string;
  mark?: string;
}

interface AvailableModel {
  label: string;
  value: string;
}

const defaultModelCfg = ref<ModelCfg[] | null>(null);
const providers = ref<Provider[]>([]);
const models = ref<ModelCfg[]>([]);
const addDialogVisible = ref(false);
const setDefaultDialogVisible = ref(false);
const addForm = ref<ModelCfg>({ id: '', mark: '', api_key: '', base_url: '' });
const setDefaultForm = ref({ modelType: '', selectedModelName: '', model_cfg_id: '' });
const availableModels = ref<AvailableModel[]>([]);

const modelColumns = [
  { title: '供应商', dataIndex: 'mark', key: 'mark', customRender: ({ text }) => getProviderName(text) },
  { title: 'API Key', dataIndex: 'api_key', key: 'api_key' },
  { title: 'Base URL', dataIndex: 'base_url', key: 'base_url' },
  { title: '操作', key: 'action', scopedSlots: { customRender: 'action' } },
];

const groupedDefaultModelCfg = computed(() => {
  if (!defaultModelCfg.value) {
    return { llm: [], embedding: [] }; //  返回空数组，避免空指针错误
  }

  const llmModels: ModelCfg[] = [];
  const embeddingModels: ModelCfg[] = [];

  defaultModelCfg.value.forEach(model => {
    if (model.type === 'llm') {
      llmModels.push(model);
    } else if (model.type === 'embedding') {
      embeddingModels.push(model);
    }
  });

  return {
    llm: llmModels,
    embedding: embeddingModels,
  };
});

const handleDeleteAvailableModel = async (model: ModelCfg) => {
  try {
    const { data } = await deleteAvailableModelCfg({ id: model.id });
    if (data.status_code !== 200) throw new Error(data.status_message || '删除可用模型失败');

    message.success('可用模型删除成功');
    await fetchDefaultModelCfg(); // Refresh the model list
  } catch (error) {
    handleAPIError(error);
  }
};


const handleAPIError = (error: any) => {
  const errorMessage = error.response?.data?.message || '请求处理失败，请稍后重试';
  console.log(errorMessage);
  throw error;
};

onMounted(async () => {
  await Promise.all([fetchProviders(), fetchModels(), fetchDefaultModelCfg()]);
});

const getProviderName = (providerMark: string) => {
  return providers.value.find(p => p.mark === providerMark)?.provider || '未知供应商';
};

const fetchProviders = async () => {
  try {
    const { data } = await listProviders();
    if (data.status_code !== 200) throw new Error(data.status_message || '获取供应商失败');
    providers.value = data.data;
  } catch (error) {
    handleAPIError(error);
  }
};

const fetchDefaultModelCfg = async () => {
  try {
    const { data } = await getAvailableModelCfgList();
    if (data.status_code !== 200) throw new Error(data.status_message || '获取可用模型列表失败');
    defaultModelCfg.value = data.data;

    const availableModelStore = useAvailableModelStore();
    availableModelStore.setAvailableModelCfg(data.data);

  } catch (error) {
    handleAPIError(error);
  }
};

const fetchModels = async () => {
  try {
    const { data } = await listModelCfg();
    if (data.status_code !== 200) throw new Error(data.status_message || '获取模型失败');
    models.value = data.data;
  } catch (error) {
    handleAPIError(error);
  }
};

const fetchAvailableModels = async (model: ModelCfg) => {
  try {
    const { data } = await getAvailableModelCfg({ id: model.id });
    if (data.status_code !== 200) throw new Error(data.status_message || '获取可用模型失败');
    
    if (!Array.isArray(data.data?.data)) {
      throw new Error('无效的模型数据格式');
    }
    
    availableModels.value = data.data.data.map(m => ({ label: m.id, value: m.id }));
  } catch (error) {
    handleAPIError(error);
  }
};

const handleAddModel = (provider: Provider) => {
  addForm.value = {
    id: '',
    provider_id: provider.id,
    name: provider.provider,
    api_key: '',
    base_url: '',
  };
  addDialogVisible.value = true;
};

const saveAddModel = async () => {
  try {
    const { data } = await createModelCfg(addForm.value);
    if (data.status_code !== 200) throw new Error(data.status_message || '创建配置失败');
    
    await fetchModels();
    addDialogVisible.value = false;
    message.success('配置创建成功');
  } catch (error) {
    handleAPIError(error);
  }
};

const handleDeleteModel = async (record) => {
  Modal.confirm({
    title: '确认删除',
    content: '删除该供应商渠道，会同步删除所有级联配置，是否确认删除？',
    okText: '确认',
    cancelText: '取消',
    async onOk() {
      try {
        const { data } = await deleteModelCfg({ id: record.id });
        if (data.status_code !== 200) throw new Error(data.status_message || '删除配置失败');
        
        message.success('删除成功');
        await fetchModels();
      } catch (error) {
        handleAPIError(error);
      }
    },
  });
};

const handleSetDefault = async (model: ModelCfg) => {
  try {
    await fetchAvailableModels(model);
    setDefaultForm.value = {
      ...setDefaultForm.value,
      model_cfg_id: model.id
    };
    setDefaultDialogVisible.value = true;
  } catch (error) {
    handleAPIError(error);
  }
};

const addAvailableModel = async () => {
  try {
    const { data } = await addAvailableModelCfg({
      setting_id: setDefaultForm.value.model_cfg_id,
      name: setDefaultForm.value.selectedModelName,
      type: setDefaultForm.value.modelType,
    });
    
    if (data.status_code !== 200) throw new Error(data.status_message || '模型添加失败');
    
    setDefaultDialogVisible.value = false;
    await fetchDefaultModelCfg();

    message.success('模型添加成功');
  } catch (error) {
    handleAPIError(error);
  }
};
</script>

<style scoped>
.model-cfg-container {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.providers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin: 24px 0;
  justify-content: center;
}

.provider-card {
  width: 100%; /* 卡片宽度自适应 */
  flex: 1 1 300px;
  max-width: 320px;
  min-height: 180px;
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.provider-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.provider-card h3 {
  font-size: 1.4rem;
  margin-bottom: 16px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.default-model-card {
  margin: 24px 0;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.default-model-card h3 {
  color: #3b82f6;
  font-size: 1.2rem;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.default-model-card p {
  margin: 10px 0;
  color: #4b5563;
  line-height: 1.6;
}

.models-container {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  margin-top: 24px;
}

.action-btn {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  border-radius: 8px;
  padding: 8px 24px;
  height: auto;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.action-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .providers-container {
    gap: 16px;
    padding: 0 12px;
  }
  
  .provider-card {
    flex-basis: 100%;
    max-width: 100%;
    min-height: 140px;
    padding: 20px;
  }

  .default-model-card {
    margin: 16px 0;
    border-radius: 12px;
  }

  .models-container {
    border-radius: 12px;
    margin: 16px 0;
  }
}

strong {
  color: #1e40af;
  margin-right: 8px;
  font-weight: 600;
}

.ant-table-thead > tr > th {
  background: #f8fafc !important;
  font-weight: 600 !important;
}
</style>