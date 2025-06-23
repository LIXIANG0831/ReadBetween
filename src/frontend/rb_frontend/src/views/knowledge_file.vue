<template>
  <div class="knowledge-file-container">
    <h2>📑 知识库文件列表</h2>

    <div class="action-bar">
      <t-button theme="primary" @click="goBack" class="action-btn">
        <template #icon><t-icon name="chevron-left" /></template>
        返回
      </t-button>
      <t-button theme="success" @click="openUploadDialog" class="action-btn">
        <template #icon><t-icon name="upload" /></template>
        上传文件
      </t-button>
    </div>

    <t-table 
      :data="fileListData" 
      :columns="columns" 
      row-key="id"
      :pagination="pagination"
      @page-change="handlePageChange"
      class="file-table"
    >
      <template #status="{ row }">
        <t-tag :theme="getStatusTheme(row.status)">
          {{ getStatusText(row.status) }}
        </t-tag>
        <t-popup v-if="row.extra" :content="row.extra" placement="top">
          <t-icon name="help-circle" style="color: var(--td-text-color-placeholder); cursor: help;" />
        </t-popup>
      </template>
      <template #operation="{ row }">
        <t-button variant="text" theme="danger" @click="deleteFile(row.id)">
          <template #icon><t-icon name="delete" /></template>
          删除
        </t-button>
      </template>
    </t-table>

    <!-- 上传文件弹窗 -->
    <t-dialog
      header="🚀 上传文件"
      v-model:visible="uploadDialogVisible"
      :on-cancel="resetUploadForm"
      class="dialog-size-xl"
    >
      <t-form layout="vertical">
        <t-form-item label="📤文件上传" class="form-item-spacing" label-width="120px">
          <t-upload
            v-model="uploadForm.fileList"
            :before-upload="beforeUpload"
            @remove="handleFileRemove"
            multiple
            theme="file"
          >
            <t-button>
              <template #icon><t-icon name="upload" /></template>
              点击上传
            </t-button>
          </t-upload>
        </t-form-item>
        <!-- 显示已上传文件列表 -->
        <div class="uploaded-files" v-if="uploadForm.uploadedFiles.length > 0">
          <h4 class="uploaded-title">📁 已上传文件</h4>
          <div class="file-list-container">
            <div v-for="(file, index) in uploadForm.uploadedFiles" :key="index" class="file-item">
              <div class="file-info">
                <t-icon name="file" class="file-icon" />
                <span class="file-name">{{ file.file_name }}</span>
              </div>
              <t-button 
                variant="text" 
                theme="danger" 
                @click="removeUploadedFile(index)"
                class="remove-btn"
              >
                <template #icon><t-icon name="delete" /></template>
                移除
              </t-button>
            </div>
          </div>
        </div>
        
        <!-- 其他表单项目保持不变 -->
        <t-form-item label="🍕切片大小" class="form-item-spacing" label-width="120px">
          <t-input-number v-model="uploadForm.chunkSize" :min="100" :max="10000" />
        </t-form-item>
        <t-form-item label="🔄🍕重复切片大小" class="form-item-spacing" label-width="120px">
          <t-input-number v-model="uploadForm.repeatSize" :min="100" :max="10000" />
        </t-form-item>
        <t-form-item label="⚡分隔符" class="form-item-spacing" label-width="120px">
          <t-input v-model="uploadForm.separator" placeholder="请输入分隔符，例如：\n\n" />
        </t-form-item>
        <t-form-item label="🤖自动执行" class="form-item-spacing" label-width="120px">
          <t-switch v-model="uploadForm.auto" />
        </t-form-item>
      </t-form>
      
      <template #footer>
        <t-button variant="outline" @click="uploadDialogVisible = false">取消</t-button>
        <t-button theme="primary" @click="saveConfiguration">保存</t-button>
      </template>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { MessagePlugin } from 'tdesign-vue-next';

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
  extra?: string | null;
}

interface UploadedFile {
  file_name: string;
  file_path: string;
  object_nameh: string;
}

interface UploadForm {
  fileList: Array<{ file: File }>;
  uploadedFiles: UploadedFile[];
  chunkSize: number;
  repeatSize: number;
  separator: string;
  auto: boolean;
}

const columns = [
  {
    colKey: 'name',
    title: '文件名',
  },
  {
    colKey: 'status',
    title: '状态',
  },
  {
    colKey: 'create_time',
    title: '创建时间',
  },
  {
    colKey: 'operation',
    title: '操作',
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
  pageSize: 5,
  total: 0,
});

const getStatusTheme = (status: number) => {
  switch (status) {
    case 1:
      return 'success'; // 成功
    case -1:
      return 'danger'; // 失败
    default:
      return 'primary'; // 默认
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
    MessagePlugin.error('知识库ID未提供');
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
      MessagePlugin.error(response.data.msg || '获取文件列表失败');
    }
  } catch (error) {
    MessagePlugin.error('请求文件列表时发生错误');
  }
};

const deleteFile = async (id: string) => {
  try {
    const response = await deleteKnowledgeFile({ id });
    if (response.data.status_code === 200) {
      MessagePlugin.success('文件删除成功');
      fetchFileList();
    } else {
      MessagePlugin.error(response.data.msg || '删除失败');
    }
  } catch (error) {
    MessagePlugin.error('删除时发生错误');
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

const beforeUpload = async (file: File) => {
  const kbId = route.params.kbId as string;
  if (!kbId) {
    MessagePlugin.error('知识库ID未提供');
    return false;
  }

  try {

    const response = await uploadKnowledgeFile({file: file.raw});
    
    if (response.data.status_code === 200) {
      MessagePlugin.success('文件上传成功');
      uploadForm.value.uploadedFiles.push(response.data.data);
      console.log(uploadForm.value.uploadedFiles)
      return true;
    } else {
      MessagePlugin.error(response.data.msg || '文件上传失败');
      return false;
    }
  } catch (error) {
    MessagePlugin.error('文件上传请求失败');
    return false;
  }
};

const removeUploadedFile = (index: number) => {
  uploadForm.value.uploadedFiles.splice(index, 1);
  MessagePlugin.success('已移除文件');
};

const handleFileRemove = (context: { index: number, file: File }) => {
  // 从 fileList 中移除
  uploadForm.value.fileList.splice(context.index, 1);
  
  // 从 uploadedFiles 中移除对应的文件（如果有）
  const index = uploadForm.value.uploadedFiles.findIndex(
    f => f.file_name === context.file.name
  );
  if (index !== -1) {
    uploadForm.value.uploadedFiles.splice(index, 1);
  }
};

const saveConfiguration = async () => {
  const kbId = route.params.kbId as string;
  if (!kbId) {
    MessagePlugin.error('知识库ID未提供');
    return;
  }

  if (uploadForm.value.uploadedFiles.length === 0) {
    MessagePlugin.warning('请先上传文件');
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
      MessagePlugin.success('配置保存成功');
      uploadDialogVisible.value = false;
      await fetchFileList();
    } else {
      MessagePlugin.error(response.data.msg || '保存失败');
    }
  } catch (error) {
    MessagePlugin.error('保存配置时发生错误');
  }
};

const handlePageChange = (pageInfo: { current: number, pageSize: number }) => {
  pagination.value.current = pageInfo.current;
  pagination.value.pageSize = pageInfo.pageSize;
  fetchFileList();
};

let refreshInterval: number | null = null;

onMounted(() => {
  fetchFileList();
  // 设置每5秒刷新一次
  refreshInterval = window.setInterval(fetchFileList, 5000);
});

onUnmounted(() => {
  // 清除定时器
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<style scoped>
.knowledge-file-container {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: var(--td-bg-color-container);
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
  gap: 12px;
}

.action-btn {
  border-radius: 8px;
  padding: 8px 24px;
  height: auto;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.file-table {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.uploaded-files {
  margin-top: 1px;
  border: 1px solid var(--td-component-stroke);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.uploaded-title {
  margin: 16px 0 12px;
  font-size: 14px;
  color: var(--td-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-list-container {
  border: 1px solid var(--td-component-border);
  border-radius: 8px;
  overflow: hidden;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background-color: var(--td-bg-color-container);
  transition: background-color 0.2s;
}

.file-item:not(:last-child) {
  border-bottom: 1px solid var(--td-component-stroke);
}

.file-item:hover {
  background-color: var(--td-bg-color-container-hover);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  color: var(--td-brand-color);
  font-size: 18px;
}

.file-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remove-btn {
  flex-shrink: 0;
  margin-left: 12px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .remove-btn {
    margin-left: 0;
    align-self: flex-end;
  }
}

.form-item-spacing {
  margin-bottom: 40px; /* 增加底部间距 */
}
</style>