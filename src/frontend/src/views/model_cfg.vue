<template>
  <div class="common-layout">
    <h3>🏢 默认供应商</h3>
    <div class="providers-container">
      <t-card
        v-for="provider in providers" 
        :key="provider.id" 
        class="provider-card"
        :bordered="false"
        hover-shadow
      >
        <div class="provider-card-content">
          <div class="provider-icon">
            <span v-if="provider.mark === 'openai'">
                <img src="@/assets/openai.svg" alt="OpenAI Icon" />
            </span>
            <span v-else-if="provider.mark === 'openai-compatible'">
                <img src="@/assets/openai-compatible.svg" alt="OpenAI-Compatible Icon" />
            </span>
            <span v-else-if="provider.mark === 'qwen'">
                <img src="@/assets/qwen.svg" alt="Qwen Icon" />
            </span>
            <span v-else-if="provider.mark === 'hosted_vllm'">
                <img src="@/assets/vllm.svg" alt="vLLM Icon" />
            </span>
          </div>
          <h4 class="provider-name">
            <span v-if="provider.provider === 'OpenAI-Compatible'">OpenAI兼容</span>
            <span v-else-if="provider.provider === 'Qwen'">通义千问</span>
            <span v-else>{{ provider.provider }}</span>
          </h4>
          <t-button theme="primary" @click="handleAddModel(provider)" class="action-btn" variant="outline">
            <template #icon><t-icon name="setting" /></template>
            添加配置
          </t-button>
        </div>
      </t-card>
    </div>

    <div class="models-container">
      <h3>🧠 已配置供应商</h3>
      <t-table 
        :data="models" 
        :columns="modelColumns" 
        row-key="id"
        :bordered="true"
        hover
      >
        <template #operation="{ row }">
          <t-button @click="handleSetDefault(row)" variant="outline">
            <template #icon><t-icon name="star" /></template>
            添加模型
          </t-button>
          <t-button @click="handleDeleteModel(row)" theme="danger" variant="outline" style="margin-left: 10px;">
            <template #icon><t-icon name="delete" /></template>
            删除
          </t-button>
        </template>
      </t-table>
    </div>

    <!-- 默认模型展示区域 -->
    <div class="models-container">
      <h3>⭐ 已添加模型</h3>
      <t-card v-if="groupedDefaultModelCfg" class="default-model-card" :bordered="false" hover-shadow>
        <t-collapse :borderless="true" expand-icon-placement="right">
          <!-- 大语言模型区域 -->
          <t-collapse-panel header="大语言模型 (LLM)" value="1" class="model-type-panel">
            <div v-if="groupedDefaultModelCfg.llm.length > 0" class="model-type-section">
              <t-card
                v-for="model in groupedDefaultModelCfg.llm"
                :key="model.id"
                class="available-model-card"
                :bordered="false"
                hover-shadow
              >
                <template #header>
                  <div class="available-model-card__header">
                    <div class="available-model-card__title">
                      <t-tag theme="primary" variant="outline">{{ model.name }}</t-tag>
                    </div>
                  </div>
                </template>
                <div class="available-model-card__body">
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="city-1" class="available-model-card__icon" />
                      <span class="available-model-card__label">供应商</span>
                    </div>
                    <span class="available-model-card__value">{{ getProviderName(model.mark) }}</span>
                  </div>
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="key" class="available-model-card__icon" />
                      <span class="available-model-card__label">API Key</span>
                    </div>
                    <span class="available-model-card__value code-style">{{ model.api_key }}</span>
                  </div>
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="link" class="available-model-card__icon" />
                      <span class="available-model-card__label">Base URL</span>
                    </div>
                    <span class="available-model-card__value code-style">{{ model.base_url }}</span>
                  </div>
                </div>
                <t-popconfirm
                  content="删除该大语言模型，会同步删除已创建的会话渠道，是否确认删除？"
                  @confirm="handleDeleteAvailableModel(model)"
                >
                  <t-button variant="text" theme="danger" class="action-button">
                    <template #icon><t-icon name="delete" /></template>
                    删除
                  </t-button>
                </t-popconfirm>
              </t-card>
            </div>
            <div v-else class="empty-tip">
              <t-icon name="error-circle" size="24px" />
              <p>暂无可用大语言模型</p>
            </div>
          </t-collapse-panel>

          <!-- 向量模型区域 -->
          <t-collapse-panel header="嵌入模型 (Embedding)" value="2" class="model-type-panel">
            <div v-if="groupedDefaultModelCfg.embedding.length > 0" class="model-type-section">
              <t-card
                v-for="model in groupedDefaultModelCfg.embedding"
                :key="model.id"
                class="available-model-card"
                :bordered="false"
                hover-shadow
              >
                <template #header>
                  <div class="available-model-card__header">
                    <div class="available-model-card__title">
                      <t-tag theme="success" variant="outline">{{ model.name }}</t-tag>
                    </div>
                  </div>
                </template>
                <div class="available-model-card__body">
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="city-1" class="available-model-card__icon" />
                      <span class="available-model-card__label">供应商</span>
                    </div>
                    <span class="available-model-card__value">{{ getProviderName(model.mark) }}</span>
                  </div>
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="key" class="available-model-card__icon" />
                      <span class="available-model-card__label">API Key</span>
                    </div>
                    <span class="available-model-card__value code-style">{{ model.api_key }}</span>
                  </div>
                  <div class="available-model-card__item">
                    <div class="item-label">
                      <t-icon name="link" class="available-model-card__icon" />
                      <span class="available-model-card__label">Base URL</span>
                    </div>
                    <span class="available-model-card__value code-style">{{ model.base_url }}</span>
                  </div>
                </div>
                <t-popconfirm
                  content="删除该嵌入模型，会同步删除已创建的知识库，是否确认删除？"
                  @confirm="handleDeleteAvailableModel(model)"
                >
                  <t-button variant="text" theme="danger" class="action-button">
                    <template #icon><t-icon name="delete" /></template>
                    删除
                  </t-button>
                </t-popconfirm>
              </t-card>
            </div>
            <div v-else class="empty-tip">
              <t-icon name="error-circle" size="24px" />
              <p>暂无可用嵌入模型</p>
            </div>
          </t-collapse-panel>
        </t-collapse>
      </t-card>
    </div>

    <!-- 添加配置弹窗 -->
    <t-dialog
      class="dialog-size-lg"
      v-model:visible="addDialogVisible"
      header="添加供应商配置"
      :on-confirm="saveAddModel"
      :on-close="() => addDialogVisible = false"
    >
      <t-form :data="addForm" :label-width="80"
      :rules="{base_url: [{ required: true, message: '请输入BaseURL', trigger: 'blur' }],api_key: [{ required: true, message: '请输入API秘钥', trigger: 'blur' }]}">
        <t-form-item label="供应商" name="name">
          <t-input v-model="addForm.name" disabled />
        </t-form-item>
        <t-form-item label="BaseURL" name="base_url" required>
          <t-input v-model="addForm.base_url" />
        </t-form-item>
        <t-form-item label="API密钥" name="api_key" required>
          <t-input v-model="addForm.api_key" />
        </t-form-item>
      </t-form>
      <template #footer>
        <t-button @click="addDialogVisible = false" variant="outline">取消</t-button>
        <t-button @click="saveAddModel" theme="primary" style="margin-left: 10px">保存</t-button>
      </template>
    </t-dialog>

    <!-- 设置默认弹窗 -->
    <t-dialog
      class="dialog-size-lg"
      v-model:visible="setDefaultDialogVisible"
      header="添加可用模型"
      :on-confirm="addAvailableModel"
      :on-close="() => setDefaultDialogVisible = false"
    >
      <t-form :data="setDefaultForm" :label-width="80" 
      :rules="{modelType: [{ required: true, message: '请选择模型类型', trigger: 'change' }],selectedModelName: [{ required: true, message: '请选择模型', trigger: 'change' }]}">
        <t-form-item label="模型类型" name="modelType" required>
          <t-select
            v-model="setDefaultForm.modelType" 
            placeholder="请选择模型类型"
            :options="[
              { label: '💬 大语言模型 (LLM)', value: 'llm' },
              { label: '🧬 嵌入模型 (Embedding)', value: 'embedding' },
            ]"
          />
        </t-form-item>

        <t-form-item label="选择模型" name="selectedModelName" required>
          <t-select
            v-model="setDefaultForm.selectedModelName"
            placeholder="请选择模型"
            :options="availableModels"
          />
        </t-form-item>
      </t-form>
      <template #footer>
        <t-button @click="setDefaultDialogVisible = false" variant="outline">取消</t-button>
        <t-button @click="addAvailableModel" theme="primary" style="margin-left: 10px">保存</t-button>
      </template>
    </t-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, h } from 'vue';
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
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next';
import { 
  Icon as TIcon,
  Card as TCard,
  Button as TButton,
  Collapse as TCollapse,
  CollapsePanel as TCollapsePanel,
  Table as TTable,
  Dialog as TDialog,
  Form as TForm,
  FormItem as TFormItem,
  Input as TInput,
  Select as TSelect,
  Popconfirm as TPopconfirm
} from 'tdesign-vue-next';

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
  type?: string;
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
const addForm = ref<Omit<ModelCfg, 'id'>>({ 
  provider_id: '',
  name: '',
  api_key: '', 
  base_url: '',
  mark: '' 
});
const setDefaultForm = ref({ 
  modelType: '', 
  selectedModelName: '', 
  model_cfg_id: '' 
});
const availableModels = ref<AvailableModel[]>([]);

const modelColumns = [
  { title: '供应商', colKey: 'mark', cell: (h, { row }) => getProviderName(row.mark) },
  { title: 'API Key', colKey: 'api_key' },
  { title: 'Base URL', colKey: 'base_url' },
  { 
    title: '操作', 
    colKey: 'operation', 
    cell: (h, { row }) => h('div', { class: 'operation-cell' }, [
      h(
        TButton,
        {
          onClick: () => handleSetDefault(row),
          icon: () => h(TIcon, { name: 'star' })
        },
        { default: () => '添加模型' }
      ),
      h(
        TButton,
        {
          onClick: () => handleDeleteModel(row),
          theme: 'danger',
          variant: 'outline',
          style: 'margin-left: 10px;',
          icon: () => h(TIcon, { name: 'delete' })
        },
        { default: () => '删除' }
      )
    ]) 
  },
];

const groupedDefaultModelCfg = computed(() => {
  if (!defaultModelCfg.value) {
    return { llm: [], embedding: [] };
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

    MessagePlugin.success('可用模型删除成功');
    await fetchDefaultModelCfg();
  } catch (error) {
    handleAPIError(error);
  }
};

const handleAPIError = (error: any) => {
  const errorMessage = error.response?.data?.message || '请求处理失败，请稍后重试';
  MessagePlugin.error(errorMessage);
  console.error(errorMessage);
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
    provider_id: provider.id,
    name: provider.provider,
    api_key: '',
    base_url: '',
    mark: provider.mark
  };
  addDialogVisible.value = true;
};

const saveAddModel = async () => {
  try {
    // 检查 name 和 type 是否为空
    if (!addForm.value.api_key || !addForm.value.base_url) {
      MessagePlugin.error('请填写BaseURL及API密钥');
      return; // 终止执行
    }

    const { data } = await createModelCfg(addForm.value);
    if (data.status_code !== 200) throw new Error(data.status_message || '创建配置失败');
    
    await fetchModels();
    addDialogVisible.value = false;
    MessagePlugin.success('配置创建成功');
  } catch (error) {
    handleAPIError(error);
  }
};

const handleDeleteModel = async (record: ModelCfg) => {
  const confirmDia = DialogPlugin.confirm({
    header: '确认删除',
    body: '删除该供应商渠道，会同步删除所有级联配置，是否确认删除？',
    confirmBtn: '确认',
    cancelBtn: '取消',
    onConfirm: async () => {
      try {
        const { data } = await deleteModelCfg({ id: record.id });
        if (data.status_code !== 200) throw new Error(data.status_message || '删除配置失败');
        
        MessagePlugin.success('删除成功');
        await fetchModels();
      } catch (error) {
        handleAPIError(error);
      } finally {
        confirmDia.destroy();
      }
    },
    onClose: () => {
      confirmDia.destroy();
    }
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
    // 检查 name 和 type 是否为空
    if (!setDefaultForm.value.selectedModelName || !setDefaultForm.value.modelType) {
      MessagePlugin.error('请选择模型类型和模型名称');
      return; // 终止执行
    }

    const { data } = await addAvailableModelCfg({
      setting_id: setDefaultForm.value.model_cfg_id,
      name: setDefaultForm.value.selectedModelName,
      type: setDefaultForm.value.modelType,
    });
    
    if (data.status_code !== 200) throw new Error(data.status_message || '模型添加失败');
    
    setDefaultDialogVisible.value = false;
    await fetchDefaultModelCfg();

    MessagePlugin.success('模型添加成功');
  } catch (error) {
    handleAPIError(error);
  }
};
</script>

<style scoped>
/* 供应商卡片容器 */
.providers-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin: 24px 0;
  max-width: 1200px; /* 可选，限制最大宽度 */
  margin: 0 auto; /* 水平居中 */
}

/* 供应商卡片 */
.provider-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  background: var(--td-bg-color-container);
  overflow: hidden;
  padding: 20px;
  border: none;
}

.provider-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.provider-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.provider-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.provider-name {
  font-size: 1.1rem;
  margin: 0 0 16px 0;
  color: var(--td-text-color-primary);
  font-weight: 600;
  text-align: center;
}

.action-btn {
  width: 100%;
  margin-top: auto;
}

/* 模型配置区域 */
.models-container {
  background: var(--td-bg-color-container);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  margin: 32px 0;
}

/* 可用模型配置主卡片 */
.default-model-card {
  margin: 32px 0;
  border-radius: 12px;
  background: var(--td-bg-color-container);
  overflow: hidden;
  transition: all 0.3s ease;
  border: none;
}

.default-model-card h3 {
  color: var(--td-brand-color);
  font-size: 1.25rem;
  margin: 0;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--td-component-border);
}

/* 折叠面板整体样式 */
.t-collapse {
  --td-collapse-border-radius: 0;
  --td-collapse-panel-border-radius: 0;
}

/* 折叠面板项 */
.model-type-panel {
  border-bottom: 1px solid var(--td-component-stroke);
}

.model-type-panel:last-child {
  border-bottom: none;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-type-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.llm-tag {
  background-color: var(--td-success-color-light);
  color: var(--td-success-color);
}

.embedding-tag {
  background-color: var(--td-warning-color-light);
  color: var(--td-warning-color);
}

.panel-title {
  font-weight: 500;
  font-size: 1rem;
  color: var(--td-text-color-primary);
}

.t-collapse-panel__header {
  padding: 16px 24px;
  background: var(--td-bg-color-secondarycontainer);
  transition: all 0.2s ease;
}

.t-collapse-panel__header:hover {
  background: var(--td-bg-color-container-hover);
}

.t-collapse-panel__content {
  padding: 16px 24px;
  background: var(--td-bg-color-container);
}

/* 模型类型区域 */
.model-type-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

/* 单个模型卡片 */
.available-model-card {
  border-radius: 8px;
  transition: all 0.3s ease;
  overflow: hidden;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-component-border);
}

.available-model-card__header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--td-component-border);
}

.available-model-card__title {
  font-weight: 500;
  font-size: 1rem;
  color: var(--td-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.available-model-card__body {
  padding: 16px;
}

.available-model-card__item {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
  flex-direction: column;
  gap: 4px;
}

.available-model-card__item:last-child {
  margin-bottom: 0;
}

.item-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.available-model-card__icon {
  color: var(--td-brand-color);
  font-size: 0.9em;
}

.available-model-card__label {
  font-size: 0.9rem;
  color: var(--td-text-color-secondary);
}

.available-model-card__value {
  font-size: 0.95rem;
  color: var(--td-text-color-primary);
  word-break: break-all;
  padding-left: 22px;
}

.code-style {
  font-family: monospace;
  background: var(--td-bg-color-secondarycontainer);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
}

/* 空状态提示 */
.empty-tip {
  padding: 24px;
  text-align: center;
  color: var(--td-text-color-placeholder);
  border-radius: 8px;
  background: var(--td-bg-color-secondarycontainer);
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-tip p {
  margin: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .providers-container {
    grid-template-columns: 1fr;
  }
  
  .default-model-card {
    margin: 24px 0;
  }
  
  .default-model-card h3 {
    padding: 12px 16px;
  }
  
  .model-type-section {
    grid-template-columns: 1fr;
  }
  
  .t-collapse-panel__header,
  .t-collapse-panel__content {
    padding: 12px 16px;
  }
  
  .available-model-card__body {
    padding: 12px;
  }
}
</style>