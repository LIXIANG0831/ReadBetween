import { createRouter, createWebHistory, type Router, type RouteRecordRaw } from 'vue-router';
import NProgress from 'nprogress';
import exceptionRoutes from './route.exception';
import asyncRoutes from './route.async';
import commonRoutes from './route.common';
import { useAvailableModelStore } from '../store/useAvailableModelStore';
import { message } from 'ant-design-vue';

const routes: Array<RouteRecordRaw> = [
  // 无鉴权的业务路由 ex:登录
  ...commonRoutes,
  // 带鉴权的业务路由
  ...asyncRoutes,
  // 异常页必须放在路由匹配规则的最后
  ...exceptionRoutes,
];

const router: Router = createRouter({
  // 新的vue-router4 使用 history路由模式 和 base前缀
  history: createWebHistory(import.meta.env.VITE_BASE),
  routes,
});

/**
 * @description: 全局路由前置守卫，在进入路由前触发，导航在所有守卫 resolve 完之前一直处于等待中。
 * @param {RouteLocationNormalized} to  即将要进入的目标
 * @param {RouteLocationNormalizedLoaded} from  当前导航正在离开的路由
 * @return {*}
 */
router.beforeEach((to, from) => {
  console.log('全局路由前置守卫：to,from\n', to, from);
  // 设置页面标题
  document.title = (to.meta.title as string) || import.meta.env.VITE_APP_TITLE;
  const defaultModelStore = useAvailableModelStore();
  // 如果正在加载中，直接返回 true，允许导航继续
  if (defaultModelStore.isLoading) {
    return true;
  }
  // console.log('当前默认模型配置:', defaultModelStore.defaultModelCfg);
  if (to.name !== 'model_cfg' && !defaultModelStore.allAvailableModelCfg) {
    message.error('未设置默认模型配置，请前往配置页面设置。');
    return { name: 'model_cfg' }; // 跳转到配置页面
  }
  // console.log('默认模型配置已设置:', defaultModelStore.defaultModelCfg);
  if (!NProgress.isStarted()) {
    NProgress.start();
  }
});

router.afterEach((to, from) => {
  console.log('全局路由后置守卫：to,from\n', to, from);
  NProgress.done();
});

export default router;
