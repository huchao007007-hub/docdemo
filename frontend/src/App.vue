<template>
  <div id="app">
    <el-container>
      <el-header v-if="$route.path !== '/login'">
        <div class="header-content">
          <h1>📄 PDF文档智能总结</h1>
          <p class="subtitle">基于DeepSeek AI的文档总结工具</p>
          <div class="user-info">
            <el-dropdown @command="handleCommand">
              <span class="user-name">
                <el-icon><User /></el-icon>
                {{ authStore.user?.username || '用户' }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const handleCommand = (command) => {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(() => {
  console.log('PDF总结小程序启动')
  // 初始化认证状态
  authStore.init()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.el-container {
  min-height: 100vh;
}

.el-header {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  height: auto !important;
  min-height: 100px;
  position: relative;
  z-index: 100;
}

.header-content {
  text-align: center;
  width: 100%;
  position: relative;
}

.user-info {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
}

.user-name:hover {
  color: #409eff;
}

.header-content h1 {
  font-size: 32px;
  color: #333;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
  display: block;
}

.el-main {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>

