// i18n
import { createI18n } from 'vue-i18n';
import messages from '@intlify/unplugin-vue-i18n/messages';

import Antd from 'ant-design-vue';
// vue router
import router from './router';
// pinia
import store from './store';
import App from './App.vue';

import 'tdesign-vue-next/es/style/index.css'
import TDesign from 'tdesign-vue-next'

// 自定义样式
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
app.use(TDesign)


app.mount('#app');
