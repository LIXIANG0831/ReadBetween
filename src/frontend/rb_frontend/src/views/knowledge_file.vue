<template>
  <div class="knowledge-file-container">

    <h2>📑  知识库文件列表</h2>

    <div class="action-bar">
      <a-button type="primary" @click="goBack" class="action-btn">
        <template #icon><LeftOutlined /></template>
        返回
      </a-button>
      <a-button type="primary" @click="openUploadDialog" class="action-btn" style="background-color: #52c41a; border-color: #52c41a;">
        <template #icon><UploadOutlined /></template>
        上传文件
      </a-button>
    </div>

    <a-table 
      :dataSource="fileListData" 
      :columns="columns" 
      bordered
      :pagination="false"
      class="file-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-button size="small" type="link" danger @click="deleteFile(record.id)">
            <template #icon><DeleteOutlined /></template>
            删除
          </a-button>
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

    <!-- 上传文件弹窗 -->
    <a-modal
      title="🚀 上传文件"
      v-model:open="uploadDialogVisible"
      width="50%"
      @cancel="resetUploadForm"
      @ok="saveConfiguration"
      class="upload-modal"
    >
      <a-form layout="vertical">
        <a-form-item label="📤文件上传">
          <a-upload
            :file-list="uploadForm.fileList"
            :before-upload="() => false"
            @change="handleFileChange"
            @remove="handleFileRemove"
            multiple
          >
            <a-button>
              <template #icon><UploadOutlined /></template>
              点击上传
            </a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="🍕切片大小">
          <a-input-number v-model:value="uploadForm.chunkSize" :min="100" :max="10000" />
        </a-form-item>
        <a-form-item label="🔄🍕重复切片大小">
          <a-input-number v-model:value="uploadForm.repeatSize" :min="100" :max="10000" />
        </a-form-item>
        <a-form-item label="⚡分隔符">
          <a-input v-model:value="uploadForm.separator" placeholder="请输入分隔符，例如：\n\n" />
        </a-form-item>
        <a-form-item label="🤖自动执行">
          <a-switch v-model:checked="uploadForm.auto" />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="uploadDialogVisible = false">取消</a-button>
        <a-button type="primary" @click="saveConfiguration">保存</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { UploadOutlined, LeftOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { useRoute, useRouter } from 'vue-router';
import type { UploadChangeParam, UploadFile } from 'ant-design-vue';
import { 
  listKnowledgeFiles, 
  deleteKnowledgeFile, 
  uploadKnowledgeFile, 
  executeKnowledgeFile 
} from '@/api/knowledge_file';

interface FileItem {
  id: string;
  name: string;
  status: number;
  create_time: string;
  update_time: string;
}

interface UploadedFile {
  file_object_name: string;
  original_name: string;
}

interface UploadForm {
  fileList: UploadFile[];
  uploadedFiles: UploadedFile[];
  chunkSize: number;
  repeatSize: number;
  separator: string;
  auto: boolean;
}

const columns = [
  {
    title: '文件名',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '状态',
    key: 'status',
  },
  {
    title: '创建时间',
    dataIndex: 'create_time',
    key: 'create_time',
  },
  {
    title: '操作',
    key: 'action',
    align: 'right',
  },
];

const route = useRoute();
const router = useRouter();

const fileListData = ref<FileItem[]>([]);
const uploadDialogVisible = ref(false);

const initialUploadForm: UploadForm = {
  fileList: [],
  uploadedFiles: [],
  chunkSize: 1000,
  repeatSize: 200,
  separator: '\n\n',
  auto: true
};

const uploadForm = ref<UploadForm>({ ...initialUploadForm });

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
})

const handlePageChange = (page: number, pageSize: number) => {
  pagination.value.current = page
  pagination.value.pageSize = pageSize
  fetchFileList()
}

const getStatusColor = (status: number) => {
  switch (status) {
    case 1:
      return '#52c41a'; // 成功
    case -1:
      return '#ff4d4f'; // 失败
    default:
      return '#1890ff'; // 默认
  }
};

const getStatusText = (status: number) => {
  switch (status) {
    case 1:
      return '🎉 已解析';
    case -1:
      return '❌ 解析失败';
    default:
      return '🔍 未解析';
  }
};

const fetchFileList = async () => {
  const kbId = route.params.kbId as string;
  if (!kbId) {
    message.error('知识库ID未提供');
    return;
  }

  try {
    const response = await listKnowledgeFiles({ 
      kb_id: kbId,
      page: pagination.value.current,
      size: pagination.value.pageSize
    });
    if (response.data.status_code === 200) {
      fileListData.value = response.data.data.data || [];
      pagination.value.total = response.data.data.total;
    } else {
      message.error(response.data.msg || '获取文件列表失败');
    }
  } catch (error) {
    message.error('请求文件列表时发生错误');
  }
};

const deleteFile = async (id: string) => {
  try {
    const response = await deleteKnowledgeFile({ id });
    if (response.data.status_code === 200) {
      message.success('文件删除成功');
      fetchFileList();
    } else {
      message.error(response.data.msg || '删除失败');
    }
  } catch (error) {
    message.error('删除时发生错误');
  }
};

const goBack = () => {
  router.push('/knowledge');
};

const openUploadDialog = () => {
  uploadDialogVisible.value = true;
};

const resetUploadForm = () => {
  uploadForm.value = { ...initialUploadForm };
};

const handleFileChange = async (info: UploadChangeParam) => {
  const kbId = route.params.kbId as string;
  if (!kbId) {
    message.error('知识库ID未提供');
    return;
  }

  uploadForm.value.fileList = info.fileList;

  try {
    const formData = new FormData();
    formData.append('file', info.file as unknown as File);

    const response = await uploadKnowledgeFile(formData);
    
    if (response.data.status_code === 200) {
      message.success('文件上传成功');
      uploadForm.value.uploadedFiles.push(response.data.data);
    } else {
      message.error(response.data.msg || '文件上传失败');
      uploadForm.value.fileList = uploadForm.value.fileList.filter(f => f.uid !== info.file.uid);
    }
  } catch (error) {
    message.error('文件上传请求失败');
    uploadForm.value.fileList = uploadForm.value.fileList.filter(f => f.uid !== info.file.uid);
  }
};

const handleFileRemove = (file: UploadFile) => {
  uploadForm.value.uploadedFiles = uploadForm.value.uploadedFiles.filter(
    f => file.name !== f.original_name
  );
};

const saveConfiguration = async () => {
  const kbId = route.params.kbId as string;
  if (!kbId) {
    message.error('知识库ID未提供');
    return;
  }

  if (uploadForm.value.uploadedFiles.length === 0) {
    message.warning('请先上传文件');
    return;
  }

  try {
    const response = await executeKnowledgeFile({
      kb_id: kbId,
      file_object_names: uploadForm.value.uploadedFiles,
      auto: uploadForm.value.auto,
      chunk_size: uploadForm.value.chunkSize,
      repeat_size: uploadForm.value.repeatSize,
      separator: uploadForm.value.separator
    });

    if (response.data.status_code === 200) {
      message.success('配置保存成功');
      uploadDialogVisible.value = false;
      await fetchFileList();
    } else {
      message.error(response.data.msg || '保存失败');
    }
  } catch (error) {
    message.error('保存配置时发生错误');
  }
};

onMounted(() => {
  fetchFileList();
});
</script>

<style scoped>
.knowledge-file-container {
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
  color: white;
  font-weight: bold;
}

.file-table {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.upload-modal {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>