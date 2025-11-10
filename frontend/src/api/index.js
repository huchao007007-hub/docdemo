import axios from 'axios'

// 根据环境变量或自动检测API地址
const getApiBaseURL = () => {
  // 如果设置了环境变量，使用环境变量
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL + '/api'
  }
  // 生产环境使用相对路径（通过nginx代理）
  if (import.meta.env.PROD) {
    return '/api'
  }
  // 开发环境
  return '/api'
}

const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 60000, // 60秒超时，因为AI总结可能需要较长时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 从localStorage或sessionStorage恢复token
const token = localStorage.getItem('token') || sessionStorage.getItem('token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 确保每次请求都带上token
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 401未授权，清除token并跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
      // 如果不在登录页，跳转到登录页
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default api

