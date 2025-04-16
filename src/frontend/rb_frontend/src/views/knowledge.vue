<template>
  <div class="knowledge-container">
    <h2>📚  知识库列表</h2>
    <!-- 创建知识库按钮和搜索框 -->
    <div class="action-bar">
      <a-button type="primary" @click="handleCreate" class="create-button">
        <template #icon><PlusOutlined /></template>
        创建知识库 📚
      </a-button>
      <a-input
        v-model:value="search"
        placeholder="🔍 输入知识库名称搜索"
        style="width: 200px"
        class="search-input"
      />
    </div>

    <a-table :dataSource="filterTableData" :columns="columns" rowKey="id" :pagination="false" class="knowledge-table">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'enable_layout'">
          <span v-if="record.enable_layout === 1" class="text-success">✅</span>
          <span v-else class="text-muted">❌</span>
        </template>
        <template v-if="column.key === 'action'">
          <a-button type="link" @click="handleView(record.id)" class="action-button">
            <template #icon><EyeOutlined /></template>
            查看
          </a-button>
          <a-button type="link" @click="handleEdit(record)" class="action-button">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
          <a-popconfirm
            title="是否确认删除？"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" danger class="action-button">
              <template #icon><DeleteOutlined /></template>
              删除
            </a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <!-- 分页组件 -->
    <a-pagination
      v-model:current="pagination.current"
      v-model:pageSize="pagination.pageSize"
      :total="pagination.total"
      show-size-changer
      @change="handlePageChange"
      @showSizeChange="handlePageChange"
      class="pagination"
    />

    <!-- 编辑弹窗 -->
    <a-modal
      v-model:open="editDialogVisible"
      title="📝 编辑知识库"
      @cancel="editDialogVisible = false"
      class="edit-modal"
    >
      <a-form :model="editForm" :label-col="{ span: 4 }">
        <a-form-item label="知识库名称">
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-form-item label="嵌入模型" required>
          <a-input v-model:value="editForm.embedding_name" disabled />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="editForm.desc" />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="editDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="saveEdit">保存</a-button>
      </template>
    </a-modal>

    <!-- 创建知识库弹窗 -->
    <a-modal
      v-model:open="createDialogVisible"
      title="📚 创建知识库"
      @cancel="createDialogVisible = false"
      class="create-modal"
    >
      <a-form :model="createForm" :label-col="{ span: 4 }">
        <a-form-item label="知识库名称" required>
          <a-input v-model:value="createForm.name" />
        </a-form-item>
        <a-form-item label="嵌入模型" required>
          <a-select
            v-model:value="createForm.available_model_id"
            placeholder="请选择嵌入模型"
          >
            <a-select-option
              v-for="model in embeddingModelCfg"
              :key="model.id"
              :value="model.id"
            >
              {{ model.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="createForm.desc" />
        </a-form-item>
        <a-form-item label="启用版面识别">
          <a-switch
            v-model:checked="createForm.enable_layout"
            :checkedValue="1"
            :unCheckedValue="0"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="createDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="saveCreate">创建</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAvailableModelStore } from '@/store/useAvailableModelStore';
import {
  CheckOutlined,
  CloseOutlined,
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
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
  available_model_id: string
  embedding_name?: string;
  enable_layout: number
  create_time: string
  update_time: string
}

const availableModelStore = useAvailableModelStore();
const embeddingModelCfg = ref(null);
const search = ref('')
const tableData = ref<Knowledge[]>([])
const editDialogVisible = ref(false)
const createDialogVisible = ref(false)
const editForm = ref<Knowledge>({
  id: '',
  name: '',
  desc: '',
  available_model_id: '',
  embedding_name: '',
  enable_layout: 0,
  create_time: '',
  update_time: '',
})
const createForm = ref<Knowledge>({
  id: '',
  name: '',
  desc: '',
  available_model_id: '',
  enable_layout: 0,
  create_time: '',
  update_time: '',
})
const router = useRouter()

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
})

const columns = [
  {
    title: '知识库名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '描述',
    dataIndex: 'desc',
    key: 'desc',
  },
  {
    title: '嵌入模型',
    dataIndex: 'embedding_name',
    key: 'embedding_name',
  },
  {
    title: '启用版面识别',
    key: 'enable_layout',
  },
  {
    title: '创建时间',
    dataIndex: 'create_time',
    key: 'create_time',
  },
  {
    title: '更新时间',
    dataIndex: 'update_time',
    key: 'update_time',
  },
  {
    title: '操作',
    key: 'action',
    align: 'right',
  },
]

const fetchKnowledgeList = async () => {
  try {
    const response = await listKnowledge({
      page: pagination.value.current,
      size: pagination.value.pageSize,
    })
    if (response.data.status_code === 200) {
      tableData.value = response.data.data.data || []
      pagination.value.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('请求知识库列表时发生错误:', error)
  }
}

onMounted(() => {
  fetchKnowledgeList();
  // 在组件挂载时加载默认模型配置
  availableModelStore.loadAvailableModelCfg();
  embeddingModelCfg.value = availableModelStore.embeddingAvailableModelCfg;
  // console.log(embeddingModelCfg.value)
});

// TODO 正确的监听变化
// 监听 defaultModelCfg 的变化
// watch(defaultModelCfg, (newVal) => {
//   if (newVal) {
//     createForm.value.model = newVal.embedding_name || '未设置默认模型配置';
//   }
// }, { immediate: true });

const filterTableData = computed(() =>
  tableData.value.filter(
    (data) =>
      !search.value || data.name.toLowerCase().includes(search.value.toLowerCase())
  )
)

const handleView = (kbId: string) => {
  router.push(`/knowledge_file/${kbId}`)
}

const handleEdit = (row: Knowledge) => {
  editForm.value = { ...row }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  try {
    const updateResponse = await updateKnowledge(editForm.value)
    if (updateResponse.data.status_code === 200) {
      editDialogVisible.value = false
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
  createForm.value = {
    id: '',
    name: '',
    desc: '',
    available_model_id: embeddingModelCfg.value[0].id || '',
    enable_layout: 0,
    create_time: '',
    update_time: '',
  }
  createDialogVisible.value = true
}

const saveCreate = async () => {
  try {
    const createResponse = await createKnowledge(createForm.value)
    if (createResponse.data.status_code === 200) {
      createDialogVisible.value = false
      fetchKnowledgeList()
    }
  } catch (error) {
    console.error('创建时发生错误:', error)
  }
}

const handlePageChange = (page: number, pageSize: number) => {
  pagination.value.current = page
  pagination.value.pageSize = pageSize
  fetchKnowledgeList()
}
</script>


<style scoped>
.knowledge-container {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

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

.pagination {
  margin-top: 20px;
  text-align: right;
}

.text-success {
  color: #52c41a;
}

.text-muted {
  color: rgba(0, 0, 0, 0.25);
}

.edit-modal,
.create-modal {
  border-radius: 8px;
}
</style>