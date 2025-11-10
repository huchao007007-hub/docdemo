import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, register, getCurrentUser } from '../api/auth'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || sessionStorage.getItem('token') || '')
  const user = ref(null)
  const isLoggedIn = ref(!!token.value)

  // 设置token
  const setToken = (newToken, rememberMe = false) => {
    token.value = newToken
    if (newToken) {
      if (rememberMe) {
        localStorage.setItem('token', newToken)
        sessionStorage.removeItem('token')
      } else {
        sessionStorage.setItem('token', newToken)
        localStorage.removeItem('token')
      }
      // 设置axios默认header
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
    }
    isLoggedIn.value = !!newToken
  }

  // 设置用户信息
  const setUser = (userData) => {
    user.value = userData
  }

  // 登录
  const loginUser = async (username, password, rememberMe = false) => {
    try {
      const response = await login(username, password, rememberMe)
      if (response.success) {
        setToken(response.data.access_token, rememberMe)
        setUser({
          id: response.data.user_id,
          username: response.data.username
        })
        return { success: true }
      }
      return { success: false, message: '登录失败' }
    } catch (error) {
      return { success: false, message: error.message || '登录失败' }
    }
  }

  // 注册
  const registerUser = async (username, password, email = '') => {
    try {
      const response = await register(username, password, email)
      if (response.success) {
        setToken(response.data.access_token, false)
        setUser({
          id: response.data.user_id,
          username: response.data.username
        })
        return { success: true }
      }
      return { success: false, message: '注册失败' }
    } catch (error) {
      return { success: false, message: error.message || '注册失败' }
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const response = await getCurrentUser()
      if (response.success) {
        setUser(response.data)
        return true
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // token可能失效，清除
      logout()
    }
    return false
  }

  // 登出
  const logout = () => {
    setToken('')
    setUser(null)
  }

  // 初始化：从localStorage或sessionStorage恢复token
  const init = () => {
    const savedToken = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (savedToken && !token.value) {
      setToken(savedToken, !!localStorage.getItem('token'))
      fetchUserInfo()
    } else if (savedToken && token.value) {
      // 如果已有token，确保axios header设置正确
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    setToken,
    setUser,
    loginUser,
    registerUser,
    fetchUserInfo,
    logout,
    init
  }
})

