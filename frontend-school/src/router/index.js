import { createRouter, createWebHistory } from 'vue-router'

// 路由守卫：无 token 一律回登录页（需求文档 9.1 页面清单）
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '数据大屏' } },
      { path: 'price/query', name: 'PriceQuery', component: () => import('../views/PriceQuery.vue'), meta: { title: '价格查询' } },
      { path: 'price/trend', name: 'PriceTrend', component: () => import('../views/PriceTrend.vue'), meta: { title: '趋势分析' } },
      { path: 'price/compare', name: 'PriceCompare', component: () => import('../views/PriceCompare.vue'), meta: { title: '地区对比' } },
      { path: 'feed', name: 'FeedPrice', component: () => import('../views/FeedPrice.vue'), meta: { title: '饲料价格' } },
      { path: 'predict', name: 'Predict', component: () => import('../views/Predict.vue'), meta: { title: '价格预测' } },
      { path: 'analysis', name: 'Analysis', component: () => import('../views/Analysis.vue'), meta: { title: '关联分析' } },
      { path: 'alert', name: 'AlertManage', component: () => import('../views/AlertManage.vue'), meta: { title: '预警管理' } },
      { path: 'admin', name: 'Admin', component: () => import('../views/Admin.vue'), meta: { title: '后台管理' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - 甘肃牛羊价格平台` : '甘肃牛羊价格平台'
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'Login') {
    return { name: 'Login' }
  }
})

export default router
