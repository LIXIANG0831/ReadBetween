<template>
  <div class="common-layout">
    <h3>📚 知识库列表</h3>
    <!-- 创建知识库按钮和搜索框 -->
    <div class="action-bar">
      <t-button theme="primary" @click="handleCreate" class="create-button">
        <template #icon><t-icon name="add" /></template>
        创建知识库
      </t-button>
      <t-input
        v-model="searchKeyword"
        placeholder="🔍 输入知识库名称搜索"
        style="width: 200px"
        class="search-input"
      />
    </div>

    <t-table
      :data="filterTableData"
      :columns="columns"
      row-key="id"
      :pagination="paginationConfig"
      @page-change="handlePageChange"
      class="knowledge-table"
    >
      <template #enable_layout="{ row }">
        <span v-if="row.enable_layout === 1" class="text-success">✅</span>
        <span v-else class="text-muted">❌</span>
      </template>
      <template #operation="{ row }">
        <t-button variant="text" theme="primary" @click="handleView(row.id)" class="action-button">
          <template #icon><t-icon name="browse" /></template>
          查看
        </t-button>
        <t-button variant="text" theme="primary" @click="handleEdit(row)" class="action-button">
          <template #icon><t-icon name="edit" /></template>
          编辑
        </t-button>
        <t-popconfirm
          content="是否确认删除？"
          @confirm="handleDelete(row.id)"
        >
          <t-button variant="text" theme="danger" class="action-button">
            <template #icon><t-icon name="delete" /></template>
            删除
          </t-button>
        </t-popconfirm>
      </template>
    </t-table>

    <!-- 编辑弹窗 -->
    <t-dialog
      v-model:visible="isEditDialogVisible"
      header="📝 编辑知识库"
      :on-cancel="() => isEditDialogVisible = false"
      class="dialog-size-xl"
    >
      <t-form :data="editFormData" :label-width="80">
        <t-form-item label="知识库名称" name="name">
          <t-input v-model="editFormData.name" />
        </t-form-item>
        <t-form-item label="嵌入模型" required name="embedding_name">
          <t-input v-model="editFormData.embedding_name" disabled />
        </t-form-item>
        <t-form-item label="描述" name="desc">
          <t-textarea v-model="editFormData.desc" />
        </t-form-item>
      </t-form>
      <template #footer>
        <t-button variant="outline" @click="isEditDialogVisible = false">取消</t-button>
        <t-button theme="primary" @click="saveEdit">保存</t-button>
      </template>
    </t-dialog>

    <!-- 创建知识库弹窗 -->
    <t-dialog
      v-model:visible="isCreateDialogVisible"
      header="📚 创建知识库"
      :on-cancel="() => isCreateDialogVisible = false"
      class="modal-size-lg"
    >
      <t-form :data="createFormData" :label-width="80">
        <t-form-item label="知识库名称" required name="name">
          <t-input v-model="createFormData.name" />
        </t-form-item>
        <t-form-item label="嵌入模型" required name="available_model_id">
          <t-select
            v-model="createFormData.available_model_id"
            placeholder="请选择嵌入模型"
            clearable
            filterable
          >
            <t-option value="" label="系统内置嵌入模型" />
            <t-option
              v-for="model in embeddingModelList"
              :key="model.id"
              :value="model.id"
              :label="model.name"
            />
          </t-select>
        </t-form-item>
        <t-form-item label="描述" name="desc">
          <t-textarea v-model="createFormData.desc" />
        </t-form-item>
        <t-form-item label="启用版面识别" name="enable_layout">
          <t-switch
            v-model="createFormData.enable_layout"
            :custom-value="[1, 0]"
          />
        </t-form-item>
      </t-form>
      <template #footer>
        <t-button variant="outline" @click="isCreateDialogVisible = false">取消</t-button>
        <t-button theme="primary" @click="saveCreate">创建</t-button>
      </template>
    </t-dialog>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import {
  listKnowledge,
  updateKnowledge,
  deleteKnowledge,
  createKnowledge,
} from '@/api/knowledge'

interface Knowledge {
  id: string
  name: string
  desc: string
  available_model_id?: string | null;
  embedding_name?: string;
  enable_layout: number
  create_time: string
  update_time: string
}

const availableModelStore = useAvailableModelStore();
const embeddingModelList = ref([]);
const searchKeyword = ref('')
const knowledgeList = ref<Knowledge[]>([])
const isEditDialogVisible = ref(false)
const isCreateDialogVisible = ref(false)
const editFormData = ref<Knowledge>({
  id: '',
  name: '',
  desc: '',
  available_model_id: '',
  embedding_name: '',
  enable_layout: 0,
  create_time: '',
  update_time: '',
})
const createFormData = ref<Knowledge>({
  id: '',
  name: '',
  desc: '',
  available_model_id: '',
  enable_layout: 0,
  create_time: '',
  update_time: '',
})
const router = useRouter()

const paginationConfig = ref({
  current: 1,
  pageSize: 5,
  total: 0,
})

const columns = [
  {
    colKey: 'name',
    title: '知识库名称',
  },
  {
    colKey: 'desc',
    title: '描述',
  },
  {
    colKey: 'embedding_name',
    title: '嵌入模型',
  },
  {
    colKey: 'enable_layout',
    title: '启用版面识别',
  },
  {
    colKey: 'create_time',
    title: '创建时间',
  },
  {
    colKey: 'update_time',
    title: '更新时间',
  },
  {
    colKey: 'operation',
    title: '操作',
    align: 'right',
  },
]

const fetchKnowledgeList = async () => {
  try {
    const response = await listKnowledge({
      page: paginationConfig.value.current,
      size: paginationConfig.value.pageSize,
    })
    if (response.data.status_code === 200) {
      knowledgeList.value = response.data.data.data || []
      paginationConfig.value.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('请求知识库列表时发生错误:', error)
  }
}

onMounted(() => {
  fetchKnowledgeList();
  availableModelStore.loadAvailableModelCfg();
});

watch(
  () => availableModelStore.embeddingAvailableModelCfg,
  (newVal) => {
    if (newVal) {
      embeddingModelList.value = newVal;
    }
  },
  { immediate: true }
);

const filterTableData = computed(() =>
  knowledgeList.value.filter(
    (data) =>
      !searchKeyword.value || data.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
)

const handleView = (kbId: string) => {
  router.push(`/knowledge_file/${kbId}`)
}

const handleEdit = (row: Knowledge) => {
  editFormData.value = { ...row }
  isEditDialogVisible.value = true
}

const saveEdit = async () => {
  try {
    const updateResponse = await updateKnowledge(editFormData.value)
    if (updateResponse.data.status_code === 200) {
      isEditDialogVisible.value = false
      fetchKnowledgeList()
    }
  } catch (error) {
    console.error('更新时发生错误:', error)
  }
}

const handleDelete = async (id: string) => {
  try {
    const deleteResponse = await deleteKnowledge({ id })
    if (deleteResponse.data.status_code === 200) {
      fetchKnowledgeList()
    }
  } catch (error) {
    console.error('删除时发生错误:', error)
  }
}

const handleCreate = () => {
  createFormData.value = {
    id: '',
    name: '新知识库',
    desc: '',
    available_model_id: '',
    enable_layout: 0,
    create_time: '',
    update_time: '',
  }
  isCreateDialogVisible.value = true
}

const saveCreate = async () => {
  try {
    if (createFormData.value.available_model_id === '') {
      createFormData.value.available_model_id = null;
    }
    const createResponse = await createKnowledge(createFormData.value)
    if (createResponse.data.status_code === 200) {
      isCreateDialogVisible.value = false
      fetchKnowledgeList()
    }
  } catch (error) {
    console.error('创建时发生错误:', error)
  }
}

const handlePageChange = (pageInfo: any) => {
  paginationConfig.value.current = pageInfo.current
  paginationConfig.value.pageSize = pageInfo.pageSize
  fetchKnowledgeList()
}
</script>

<style scoped>

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.create-button {
  border-radius: 8px;
  font-weight: bold;
}

.search-input {
  border-radius: 8px;
}

.knowledge-table {
  flex: 1;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-button {
  margin-right: 8px;
}

.text-success {
  color: var(--td-success-color);
}

.text-muted {
  color: var(--td-text-color-placeholder);
}
</style>