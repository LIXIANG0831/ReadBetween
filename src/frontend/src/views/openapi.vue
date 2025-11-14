<template>
  <div class="common-layout">
    <!-- OpenAPI配置列表 -->
    <t-card title="🧾 OpenAPI配置列表" class="mb-6" :bordered="false">
      <template #actions>
        <t-button @click="showCreateDialog">
          <template #icon><t-icon name="add" /></template>
          创建配置
        </t-button>
        <t-button variant="text" @click="refreshConfigs">
          <template #icon><t-icon name="refresh" /></template>
          刷新数据
        </t-button>
      </template>

      <t-loading :loading="openapiStore.loading && !openapiStore.configs" size="small" :fullscreen="false">
        <div v-if="openapiStore.configs && openapiStore.configs.data && openapiStore.configs.data.length > 0">
          <!-- 使用折叠面板展示配置列表 -->
          <t-collapse :default-expand-all="false" expand-icon-position="right" expand-mutex>
            <t-collapse-panel
              v-for="config in openapiStore.configs.data"
              :key="config.id"
              :header="config.name"
              :value="config.id"
            >
              <div class="config-detail-container">
                <div class="detail-section">
                  <t-descriptions :column="2" layout="vertical" size="medium">
                    <t-descriptions-item label="描述">{{ config.description || '暂无描述' }}</t-descriptions-item>
                    <t-descriptions-item label="基础URL">{{ config.base_url || 'N/A' }}</t-descriptions-item>
                    <t-descriptions-item label="工具数量">
                      <t-tag theme="primary" variant="light">{{ config.tools_count }}</t-tag>
                    </t-descriptions-item>
                    <t-descriptions-item label="凭证状态">
                      <t-tag v-if="config.has_credentials" theme="success" size="small">已配置</t-tag>
                      <t-tag v-else theme="warning" size="small">未配置</t-tag>
                    </t-descriptions-item>
                    <t-descriptions-item label="创建时间">{{ formatDate(config.created_at) }}</t-descriptions-item>
                    <!-- <t-descriptions-item label="更新时间">{{ formatDate(config.updated_at) }}</t-descriptions-item> -->
                  </t-descriptions>
                </div>
                
                <div class="action-section">
                  <t-space>
                    <t-button theme="primary" variant="text" @click="showConfigDetail(config.id)">查看工具详情</t-button>
                    <t-popconfirm 
                      content="确定要删除这个配置吗？此操作不可撤销。" 
                      @confirm="handleDelete(config.id)"
                    >
                      <t-button theme="danger" variant="text">删除</t-button>
                    </t-popconfirm>
                  </t-space>
                </div>
              </div>
            </t-collapse-panel>
          </t-collapse>
        </div>
        <div v-else class="empty-container">
          <t-empty description="暂无OpenAPI配置数据" />
        </div>
      </t-loading>
    </t-card>

    <!-- OpenAPI配置详情 -->
    <t-dialog
      v-model:visible="showDetailDialog"
      header="工具列表"
      class="modal-size-xl"
      width="800px"
      :footer="false"
      @closed="closeDetailDialog"
    >
      <t-loading :loading="detailLoading" size="small" :fullscreen="false">
        <div v-if="currentConfigDetail">
          <!-- <t-card title="基本信息" :bordered="false" class="mb-4">
            <t-descriptions :column="2" layout="vertical" size="medium">
              <t-descriptions-item label="名称">{{ currentConfigDetail.data.name }}</t-descriptions-item>
              <t-descriptions-item label="基础URL">{{ currentConfigDetail.data.base_url }}</t-descriptions-item>
              <t-descriptions-item label="凭证状态">
                <t-tag v-if="currentConfigDetail.data.has_credentials" theme="success" size="small">已配置</t-tag>
                <t-tag v-else theme="warning" size="small">未配置</t-tag>
              </t-descriptions-item>
              <t-descriptions-item label="创建时间">{{ formatDate(currentConfigDetail.data.created_at) }}</t-descriptions-item>
              <t-descriptions-item label="更新时间">{{ formatDate(currentConfigDetail.data.updated_at) }}</t-descriptions-item>
              <t-descriptions-item label="描述" :span="2">{{ currentConfigDetail.data.description || '暂无描述' }}</t-descriptions-item>
            </t-descriptions>
          </t-card> -->

          <t-table
            :columns="toolColumns"
            :data="currentConfigDetail.data.tools"
            row-key="id"
            size="medium"
            :pagination="false"
            bordered
            hover
            stripe
          >
            <template #method="{ row }">
              <t-tag :theme="getMethodTagTheme(row.method)">{{ row.method }}</t-tag>
            </template>

            <template #created_at="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </t-table>
        </div>
        <div v-else class="empty-container">
          <t-empty description="暂无详细信息" />
        </div>
      </t-loading>
    </t-dialog>

    <!-- 创建OpenAPI配置弹窗 -->
    <t-dialog
      v-model:visible="showCreateDialogVisible"
      header="创建OpenAPI配置"
      class="modal-size-xl"
      width="1000px"
      @confirm="handleCreateConfig"
      @closed="closeCreateDialog"
    >
      <t-form :data="createConfigForm" :rules="createConfigRules" ref="formRef" label-align="top">
        <t-form-item label="配置名称" name="name">
          <t-input v-model="createConfigForm.name" placeholder="请输入配置名称" />
        </t-form-item>
        <t-form-item label="描述" name="description">
          <t-textarea v-model="createConfigForm.description" placeholder="请输入描述" />
        </t-form-item>
        <t-form-item label="OpenAPI规范" name="openapi_spec">
          <monaco-editor
            v-model:model-value="createConfigForm.openapi_spec"
            language="json"
            :editor-options="{
              theme: 'vs-dark',
              fontSize: 14,
              minimap: { enabled: true },
              lineNumbers: 'on',
              wordWrap: 'on',
              autoClosingBrackets: 'always',
              autoIndent: 'full',
              formatOnPaste: true,
              formatOnType: true,
              suggest: {
                showWords: false
              }
            }"
            height="200px"
          />
        </t-form-item>
        <t-form-item label="Credentials" name="credentials">
          <t-input v-model="createConfigForm.credentials" placeholder="请输入凭证">
            <template #suffix>
              <t-popup>
                <template #content>
                  <div>支持两种认证类型：</div>
                  <div>1. apiKey类型：根据OpenAPI规范中securitySchemes的定义，Credentials将作为api_key插入到header、query或cookie中</div>
                  <div>2. http类型：Credentials将作为Bearer Token添加到Authorization头部</div>
                </template>
                <t-icon name="help-circle" />
              </t-popup>
            </template>
          </t-input>
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useOpenApiStore } from '@/store/openapiStore';
import { MessagePlugin } from 'tdesign-vue-next';
import { deleteOpenApiConfig, createOpenApiConfig } from '@/api/openapi';

// 自定义日期格式化函数
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
};

const openapiStore = useOpenApiStore();
const formRef = ref();

// 表格列定义（用于详情工具列表）
const toolColumns = [
  {
    title: '名称',
    colKey: 'name',
    width: 150,
  },
  {
    title: '描述',
    colKey: 'description',
    ellipsis: true,
  },
  {
    title: '方法',
    colKey: 'method',
    width: 100,
    align: 'center',
    cell: 'method',
  },
  {
    title: '路径',
    colKey: 'path',
    width: 150,
    ellipsis: true,
  },
  {
    title: '创建时间',
    colKey: 'created_at',
    width: 180,
    ellipsis: true,
    cell: 'created_at',
  },
];

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
});

// 详情弹窗相关
const showDetailDialog = ref(false);
const detailLoading = ref(false);
const currentConfigDetail = ref<Api.OpenApiConfigToolsList | null>(null);

// 创建配置弹窗相关
const showCreateDialogVisible = ref(false);
const createConfigForm = reactive({
  name: '',
  description: '',
  openapi_spec: '{}',
  credentials: ''
});

const createConfigRules = {
  name: [{ required: true, message: '请输入配置名称' }],
  openapi_spec: [{ required: true, message: '请输入OpenAPI规范' }]
};

// 初始化数据
onMounted(async () => {
  await loadData();
});

const loadData = async () => {
  try {
    await openapiStore.fetchConfigs(pagination.value.current, pagination.value.pageSize);
    if (openapiStore.configs) {
      pagination.value.total = openapiStore.configs.total;
    }
  } catch (error) {
    MessagePlugin.error('数据加载失败');
  }
};

// 刷新配置列表
const refreshConfigs = async () => {
  try {
    await loadData();
    MessagePlugin.success('数据刷新成功');
  } catch (error) {
    MessagePlugin.error('数据刷新失败');
  }
};

// 分页变化处理
const onPageChange = (pageInfo: { current: number; pageSize: number }) => {
  pagination.value.current = pageInfo.current;
  pagination.value.pageSize = pageInfo.pageSize;
  loadData();
};

// 显示配置详情
const showConfigDetail = async (configId: string) => {
  detailLoading.value = true;
  showDetailDialog.value = true;
  try {
    // 先从缓存中查找
    if (openapiStore.configDetails[configId]) {
      currentConfigDetail.value = {
        total: 0,
        data: openapiStore.configDetails[configId]
      };
    } else {
      // 如果缓存中没有，则请求数据
      await openapiStore.fetchConfigTools(configId);
      currentConfigDetail.value = {
        total: 0,
        data: openapiStore.configDetails[configId]
      };
    }
  } catch (error) {
    MessagePlugin.error('获取配置详情失败');
  } finally {
    detailLoading.value = false;
  }
};

// 处理删除操作
const handleDelete = async (configId: string) => {
  try {
    const response = await deleteOpenApiConfig(configId);
    if (response.data.status_code === 200) {
      MessagePlugin.success(response.data.data.message);
      // 从store中移除已删除的配置
      if (openapiStore.configs) {
        openapiStore.configs.data = openapiStore.configs.data.filter(config => config.id !== configId);
        openapiStore.configs.total = openapiStore.configs.total - 1;
      }
      // 从详情中移除
      delete openapiStore.configDetails[configId];
      // 如果当前页没有数据了且不是第一页，则返回上一页
      if (openapiStore.configs && openapiStore.configs.data.length === 0 && pagination.value.current > 1) {
        pagination.value.current--;
        await loadData();
      }
    } else {
      MessagePlugin.error('删除失败');
    }
  } catch (error) {
    MessagePlugin.error('删除配置失败');
  }
};

// 显示创建配置弹窗
const showCreateDialog = () => {
  showCreateDialogVisible.value = true;
};

// 关闭创建配置弹窗
const closeCreateDialog = () => {
  showCreateDialogVisible.value = false;
  // 重置表单
  createConfigForm.name = '';
  createConfigForm.description = '';
  createConfigForm.openapi_spec = '{}';
  createConfigForm.credentials = '';
};

// 处理创建配置
const handleCreateConfig = async () => {
  try {
    // 验证表单
    const result = await formRef.value.validate();
    if (result !== true) {
      MessagePlugin.error('请检查表单填写是否正确');
      return;
    }

    // 解析openapi_spec
    let openapiSpec;
    try {
      openapiSpec = JSON.parse(createConfigForm.openapi_spec);
    } catch (error) {
      MessagePlugin.error('OpenAPI规范格式不正确，请输入有效的JSON');
      return;
    }

    // 构造请求数据
    const requestData = {
      name: createConfigForm.name,
      description: createConfigForm.description,
      openapi_spec: openapiSpec,
      credentials: createConfigForm.credentials
    };

    // 调用创建接口
    const response = await createOpenApiConfig(requestData);
    if (response.data.status_code === 200) {
      MessagePlugin.success('配置创建成功');
      closeCreateDialog();
      // 重新加载数据
      await loadData();
    } else {
      MessagePlugin.error('创建失败: ' + response.status_message);
    }
  } catch (error) {
    MessagePlugin.error('创建配置失败');
  }
};

// 关闭详情弹窗
const closeDetailDialog = () => {
  showDetailDialog.value = false;
  currentConfigDetail.value = null;
};

// 根据HTTP方法返回标签主题色
const getMethodTagTheme = (method: string) => {
  switch (method.toUpperCase()) {
    case 'GET':
      return 'success';
    case 'POST':
      return 'warning';
    case 'PUT':
      return 'primary';
    case 'DELETE':
      return 'danger';
    default:
      return 'default';
  }
};
</script>

<style scoped>
.mb-6 {
  margin-bottom: 24px;
}

.empty-container {
  padding: 40px 0;
  text-align: center;
}

/* 折叠面板美化 */
.t-collapse {
  border: none;
  background-color: transparent;
}

.t-collapse-panel {
  border-radius: 8px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.t-collapse-panel:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.t-collapse-header {
  font-size: 16px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  padding: 12px 16px;
  background-color: var(--td-bg-color-container);
  border-left: 4px solid var(--td-brand-color);
}

.t-collapse-content {
  padding: 16px;
  background-color: #fff;
}

.config-detail-container {
  padding: 8px 12px;
}

.detail-section {
  margin-bottom: 20px;
}

.action-section {
  border-top: 1px solid var(--td-border-level-1-color);
  padding-top: 16px;
}
</style>