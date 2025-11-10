import api from './index'

// 检查是否有用户
export const checkUsers = () => {
  return api.get('/auth/check-users')
}

// 用户注册
export const register = (username, password, email = '') => {
  return api.post('/auth/register', {
    username,
    password,
    email
  })
}

// 用户登录
export const login = (username, password, rememberMe = false) => {
  return api.post('/auth/login', {
    username,
    password,
    remember_me: rememberMe
  })
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return api.get('/auth/me')
}

