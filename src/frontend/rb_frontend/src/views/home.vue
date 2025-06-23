<script setup lang="ts">
import { ref } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';

const channels = ref([
  { id: 1, name: '微信渠道', status: 'active', users: 1250 },
  { id: 2, name: 'APP渠道', status: 'active', users: 3420 },
  { id: 3, name: '网页渠道', status: 'inactive', users: 780 },
]);

const columns = [
  { colKey: 'name', title: '渠道名称', width: 150 },
  { colKey: 'status', title: '状态', width: 100 },
  { colKey: 'users', title: '用户数', width: 120 },
  { colKey: 'operations', title: '操作', width: 150 },
];

const handleEdit = (id: number) => {
  MessagePlugin.success(`编辑渠道 ${id}`);
};
</script>

<template>
  <div class="common-layout">
    <t-card :bordered="false" class="welcome-card">
      <div class="welcome-content">
        <h2>欢迎回来！</h2>
        <p>今日新增用户 128 人，总对话量 2,456 次</p>
      </div>
    </t-card>

    <t-card title="渠道管理" class="channel-card" :bordered="false">
      <template #actions>
        <t-button theme="primary" variant="outline">
          <template #icon>
            <t-icon name="add" />
          </template>
          新增渠道
        </t-button>
      </template>
      
      <t-table
        :data="channels"
        :columns="columns"
        row-key="id"
        hover
        stripe
      >
        <template #status="{ row }">
          <t-tag :theme="row.status === 'active' ? 'success' : 'danger'" variant="light">
            {{ row.status === 'active' ? '活跃' : '停用' }}
          </t-tag>
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-button size="small" theme="primary" variant="text" @click="handleEdit(row.id)">
              编辑
            </t-button>
            <t-button size="small" theme="danger" variant="text">
              删除
            </t-button>
          </t-space>
        </template>
      </t-table>
    </t-card>

    <div class="metric-grid">
      <t-card :bordered="false" shadow class="metric-card">
        <div class="metric-content">
          <t-icon name="user" size="24px" class="metric-icon" />
          <div>
            <div class="metric-value">5,280</div>
            <div class="metric-label">总用户数</div>
          </div>
        </div>
      </t-card>
      
      <t-card :bordered="false" shadow class="metric-card">
        <div class="metric-content">
          <t-icon name="activity" size="24px" class="metric-icon" />
          <div>
            <div class="metric-value">1,245</div>
            <div class="metric-label">今日活跃</div>
          </div>
        </div>
      </t-card>
      
      <t-card :bordered="false" shadow class="metric-card">
        <div class="metric-content">
          <t-icon name="chat" size="24px" class="metric-icon" />
          <div>
            <div class="metric-value">3,672</div>
            <div class="metric-label">今日对话</div>
          </div>
        </div>
      </t-card>
      
      <t-card :bordered="false" shadow class="metric-card">
        <div class="metric-content">
          <t-icon name="thumb-up" size="24px" class="metric-icon" />
          <div>
            <div class="metric-value">89%</div>
            <div class="metric-label">满意率</div>
          </div>
        </div>
      </t-card>
    </div>
  </div>
</template>

<style scoped>
.welcome-card {
  margin-bottom: 16px;
  background-color: var(--td-brand-color-1);
  border-left: 4px solid var(--td-brand-color);
}

.welcome-content {
  padding: 12px 16px;
}

.welcome-content h2 {
  margin: 0 0 8px 0;
  color: var(--td-text-color-primary);
  font-size: 18px;
}

.welcome-content p {
  margin: 0;
  color: var(--td-text-color-secondary);
  font-size: 14px;
}

.channel-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  padding: 16px;
  border-radius: 8px;
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-icon {
  color: var(--td-brand-color);
  background-color: var(--td-brand-color-1);
  padding: 8px;
  border-radius: 50%;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.metric-label {
  font-size: 13px;
  color: var(--td-text-color-secondary);
  margin-top: 4px;
}
</style>