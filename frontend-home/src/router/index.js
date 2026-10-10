import { createRouter, createWebHistory } from 'vue-router'

// 家用版页面（需求文档 9.2），底部导航4个入口，其余从首页快捷进入
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  {
    path: '/',
    component: () => import('../components/TabBar.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页', tab: 'home' } },
      { path: 'price', name: 'PriceBoard', component: () => import('../views/PriceBoard.vue'), meta: { title: '价格', tab: 'price' } },
      { path: 'calculator', name: 'Calculator', component: () => import('../views/Calculator.vue'), meta: { title: '计算', tab: 'calc' } },
      { path: 'mine', name: 'Mine', component: () => import('../views/Mine.vue'), meta: { title: '我的', tab: 'mine' } },
    ],
  },
  { path: '/advice', name: 'Advice', component: () => import('../views/Advice.vue'), meta: { title: '出栏建议' } },
  { path: '/alert', name: 'AlertList', component: () => import('../views/AlertList.vue'), meta: { title: '价格预警' } },
  { path: '/livestock', name: 'Livestock', component: () => import('../views/Livestock.vue'), meta: { title: '存栏记录' } },
  { path: '/feed', name: 'Feed', component: () => import('../views/Feed.vue'), meta: { title: '饲料库存' } },
  { path: '/ledger', name: 'Ledger', component: () => import('../views/Ledger.vue'), meta: { title: '家庭账本' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = to.meta.title || '牛羊行情'
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'Login') {
    return { name: 'Login' }
  }
})

export default router
