import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  
  if (to.meta.requiresAuth) {
    // 需要登录的页面
    if (!token) {
      next('/login')
    } else {
      // 有token，初始化auth store
      if (!authStore.isLoggedIn) {
        authStore.init()
      }
      next()
    }
  } else {
    // 登录页面，如果已登录则跳转到首页
    if (token && to.path === '/login') {
      next('/')
    } else {
      next()
    }
  }
})

export default router

