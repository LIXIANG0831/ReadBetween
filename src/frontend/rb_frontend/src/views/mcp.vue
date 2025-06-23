<template>
  <div class="common-layout">
    <!-- MCP服务器配置 -->
    <a-card title="🛠 MCP服务器配置" class="mb-6">
      <MonacoEditor
        v-model:model-value="mcpStore.mcpConfig"
        language="json"
        :editorOptions="{
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
      <t-button theme="primary" @click="saveMcpConfig" style="margin-top: 16px;">保 存</t-button>
    </a-card>

    <!-- MCP服务器工具列表详情 -->
    <a-card title="🧰 MCP服务器工具列表详情">
      <div v-if="mcpStore.toolsDetail && Object.keys(mcpStore.toolsDetail).length">
        <!-- 第一层：服务名称 -->
        <a-collapse accordion>
          <a-collapse-panel v-for="(mapTools, mapName) in mcpStore.toolsDetail" :key="mapName" :header="mapName">
            <!-- 第二层：每个服务下的具体工具 -->
            <a-collapse>
              <a-collapse-panel
                v-for="(tool, toolKey) in mapTools"
                :key="`${mapName}-${toolKey}`"
                :header="toolKey"
              >
                <div style="margin-top: 16px; font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                  描述
                </div>
                <div>{{ tool.description }}</div>
                <!-- 参数说明标题 -->
                <div style="margin-top: 16px; font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                  参数说明
                </div>
                <!-- 使用表格展示参数 -->
                <a-table :columns="mcpArgsColumns" :data-source="formatParameters(tool.parameters.properties)" bordered size="middle" :pagination="false">
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.dataIndex === 'type'">
                      {{ record.type }}
                    </template>
                    <template v-if="column.dataIndex === 'description'">
                      {{ record.description }}
                    </template>
                  </template>
                </a-table>
              </a-collapse-panel>
            </a-collapse>
          </a-collapse-panel>
        </a-collapse>
      </div>
      <div v-else class="empty-text">暂无工具详情数据</div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useMcpStore } from '@/store/mcpStore';

const mcpStore = useMcpStore();

// 定义表格列
const mcpArgsColumns = [
  {
    title: '参数名',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '参数类型',
    dataIndex: 'type',
    key: 'type',
  },
  {
    title: '参数描述',
    dataIndex: 'description',
    key: 'description',
  },
];

// 初始化数据
onMounted(async () => {
  await mcpStore.fetchData();
});

// 格式化参数数据以适应表格
const formatParameters = (parameters: Record<string, any>) => {
  if (!parameters) return [];
  return Object.entries(parameters).map(([key, value]) => ({
    key: key,
    name: key,
    type: value.type,
    description: value.description,
  }));
};

// 保存配置
const saveMcpConfig = async () => {
  if (!mcpStore.mcpConfig) {
    message.warning('请填写配置内容');
    return;
  }

  const result = await mcpStore.saveMcpConfig();
  if (result.success) {
    message.success(result.message);
  } else {
    message.error(result.message);
  }
};
</script>

<style scoped>
.common-layout {
  min-height: 100vh;
  padding: 15px;
  max-width: 1800px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 16px;
}

.mb-6 {
  margin-bottom: 24px;
}

.empty-text {
  color: #999;
  font-style: italic;
}
</style>