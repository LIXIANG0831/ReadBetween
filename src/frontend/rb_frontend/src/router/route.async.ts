// 需要鉴权的业务路由
import type { RouteRecordRaw } from 'vue-router';

const asyncRoutes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'conversations',
    meta: {
      title: '对话',
      icon: '',
    },
    component: () => import('../views/conversations.vue'),
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    meta: {
      title: '知识库管理',
      icon: '',
    },
    component: () => import('../views/knowledge.vue'),
  },
  {
    path: '/knowledge_file/:kbId',
    name: 'knowledge_file',
    meta: {
      title: '知识库文件管理',
      icon: '',
    },
    component: () => import('../views/knowledge_file.vue'),
  },
  {
    path: '/model_cfg',
    name: 'model_cfg',
    meta: {
      title: '模型管理',
      icon: '',
    },
    component: () => import('../views/model_cfg.vue'),
  },
  {
    path: '/memory',
    name: 'memory',
    meta: {
      title: '记忆管理',
      icon: '',
    },
    component: () => import('../views/memory.vue'),
  },
  {
    path: '/voice',
    name: 'voice',
    meta: {
      title: '语音管理',
      icon: '',
    },
    component: () => import('../views/voice.vue'),
  },
];

export default asyncRoutes;
