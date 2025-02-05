// i18n
import { createI18n } from 'vue-i18n';
import messages from '@intlify/unplugin-vue-i18n/messages';
// import ElementPlus from 'element-plus';
// import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import Antd from 'ant-design-vue';
// vue router
import router from './router';
// pinia
import store from './store';
import App from './App.vue';

import 'element-plus/dist/index.css';
import '@/assets/styles/index.scss';

const i18n = createI18n({
  locale: 'en',
  messages,
});

const app = createApp(App);
app.use(Antd)
app.use(router);
app.use(store);
app.use(i18n);

import { useDefaultModelStore } from './store/useDefaultModelStore';
const defaultModelStore = useDefaultModelStore();
// 在应用启动时加载默认模型配置
defaultModelStore.loadDefaultModelCfg().then(() => {
  if (!defaultModelStore.defaultModelCfg) {
    // 如果默认配置为空，跳转到配置页面
    router.push({ name: 'model_cfg' });
  }
  app.mount('#app');
});