<template>
  <div class="common-layout">
    <!-- MCP服务器配置 -->
    <t-card title="🛠 MCP服务器配置" class="mb-6" :bordered="false">
      <template #actions>
        <t-button theme="primary" variant="text" @click="saveMcpConfig">
          <template #icon><t-icon name="save" /></template>
          保存配置
        </t-button>
      </template>
      <monaco-editor
        v-model:model-value="mcpStore.mcpConfig"
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
      />
    </t-card>

    <!-- MCP服务器工具列表详情 -->
    <t-card title="🧰 MCP服务器工具列表详情" :bordered="false">
      <template #actions>
        <t-button variant="text" @click="refreshToolsDetail">
          <template #icon><t-icon name="refresh" /></template>
          刷新数据
        </t-button>
      </template>

      <div v-if="mcpStore.toolsDetail && Object.keys(mcpStore.toolsDetail).length">
        <!-- 使用 TDesign 的树形折叠面板 -->
        <t-collapse :default-expand-all="false" expand-icon-position="right" expand-mutex>
          <!-- 第一层：服务名称 -->
          <t-collapse-panel
            v-for="(mapTools, mapName) in mcpStore.toolsDetail"
            :key="mapName"
            :header="mapName"
            :value="mapName"
          >
            <!-- 第二层：每个服务下的具体工具 -->
            <t-collapse :default-expand-all="false" expand-icon-position="right" expand-mutex>
              <t-collapse-panel
                v-for="(tool, toolKey) in mapTools"
                :key="`${mapName}-${toolKey}`"
                :header="toolKey"
                :value="toolKey"
              >
                <div class="tool-detail-container">
                  <div class="detail-section">
                    <h4 class="section-title">描述</h4>
                    <div class="section-content">{{ tool.description || '暂无描述' }}</div>
                  </div>

                  <div class="detail-section">
                    <h4 class="section-title">参数说明</h4>
                    <!-- 使用 TDesign 表格展示参数 -->
                    <t-table
                      :columns="mcpArgsColumns"
                      :data="formatParameters(tool.parameters?.properties, tool.parameters?.required || [])"
                      row-key="key"
                      size="medium"
                      :pagination="false"
                      bordered
                      hover
                      stripe
                    >
                      <template #empty>
                        <div class="empty-tips">该工具没有参数配置</div>
                      </template>

                      <!-- 自定义参数名列 -->
                      <template #name="{ row }">
                        <span class="param-name">{{ row.name }}</span>
                      </template>

                      <!-- 自定义必填列 -->
                      <template #required="{ row }">
                        <t-tag v-if="row.required" theme="danger" size="small">必填</t-tag>
                        <t-tag v-else theme="success" size="small">可选</t-tag>
                      </template>

                      <!-- 自定义类型列（使用带颜色的标签） -->
                      <template #type="{ row }">
                        <span :class="['param-tag', row.type]">{{ row.type }}</span>
                      </template>

                      <!-- 自定义默认值列 -->
                      <template #default="{ row }">
                        <span v-if="row.default" class="default-value">{{ row.default }}</span>
                        <span v-else>-</span>
                      </template>
                    </t-table>
                  </div>
                </div>
              </t-collapse-panel>
            </t-collapse>
          </t-collapse-panel>
        </t-collapse>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useMcpStore } from '@/store/mcpStore';

const mcpStore = useMcpStore();

// 定义表格列
const mcpArgsColumns = [
  {
    title: '参数名',
    colKey: 'name',
    width: 200,
    align: 'left',
    cell: 'name',
  },
  {
    title: '必填',
    colKey: 'required',
    width: 80,
    align: 'center',
    cell: 'required',
  },
  {
    title: '参数类型',
    colKey: 'type',
    width: 150,
    align: 'center',
    cell: 'type',
  },
  {
    title: '默认值',
    colKey: 'default',
    width: 150,
    align: 'center',
    cell: 'default',
  },
  {
    title: '参数描述',
    colKey: 'description',
    ellipsis: true,
  },
];

// 初始化数据
onMounted(async () => {
  await mcpStore.fetchData();
  console.log(mcpStore.toolsDetail)
});

// 刷新工具详情
const refreshToolsDetail = async () => {
  try {
    await mcpStore.fetchData();
    MessagePlugin.success('数据刷新成功');
  } catch (error) {
    MessagePlugin.error('数据刷新失败');
  }
};

// 格式化参数数据以适应表格，并支持类型标签逻辑
const formatParameters = (parameters: Record<string, any>, requiredParams: string[] = []) => {
  if (!parameters) return [];
  return Object.entries(parameters).map(([key, value]) => ({
    key: key,
    name: key,
    type: value.type || 'unknown',
    description: value.description || '暂无描述',
    required: requiredParams.includes(key),
    default: value.default !== undefined ? JSON.stringify(value.default) : null
  }));
};

// 保存配置
const saveMcpConfig = async () => {
  if (!mcpStore.mcpConfig) {
    MessagePlugin.warning('请填写配置内容');
    return;
  }

  const result = await mcpStore.saveMcpConfig();
  if (result.success) {
    MessagePlugin.success(result.message);
  } else {
    MessagePlugin.error(result.message);
  }
};
</script>


<style scoped>
.mb-6 {
  margin-bottom: 24px;
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

.tool-detail-container {
  padding: 8px 12px;
}

.detail-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  margin-bottom: 12px;
}

.section-content {
  color: var(--td-text-color-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

.empty-tips {
  color: var(--td-text-color-placeholder);
  padding: 16px;
  text-align: center;
}

/* 参数表格美化 */
.tool-detail-container .t-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.tool-detail-container .t-table__header th {
  background-color: var(--td-bg-color-container);
  color: var(--td-text-color-secondary);
  font-weight: 600;
  height: 40px;
}

.tool-detail-container .t-table__row td {
  padding: 12px 16px;
  vertical-align: middle;
  line-height: 1.5;
}

/* 参数名称样式 */
.param-name {
  font-family: 'Courier New', monospace;
  color: var(--td-brand-color);
  font-weight: bold;
}

/* 类型标签样式 */
.param-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
}

.param-tag.string {
  background-color: #409eff;
}
.param-tag.number {
  background-color: #1890ff;
}
.param-tag.boolean {
  background-color: #faad14;
}
.param-tag.object {
  background-color: #722ed1;
}
.param-tag.array {
  background-color: #13c2c2;
}
.param-tag.unknown {
  background-color: #8c8c8c;
}

/* 必填/可选标签样式 */
.t-tag {
  margin: 0;
  font-size: 12px;
  padding: 0 6px;
  height: 22px;
  line-height: 22px;
}

/* 默认值样式 */
.default-value {
  font-family: 'Courier New', monospace;
  color: var(--td-brand-color);
  font-size: 12px;
  background-color: var(--td-bg-color-secondarycontainer);
  padding: 2px 6px;
  border-radius: 4px;
}
</style>