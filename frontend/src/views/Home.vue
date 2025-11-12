<template>
  <div class="home">
    <el-card class="main-card" shadow="hover">
      <!-- 上传区域 -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          :limit="1"
          accept=".pdf"
          :disabled="uploading"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将PDF文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传PDF文件，且不超过10MB
            </div>
          </template>
        </el-upload>

        <div v-if="selectedFile" class="file-info">
          <el-alert
            :title="`已选择文件: ${selectedFile.name}`"
            type="info"
            :closable="false"
            show-icon
          />
          <div class="action-buttons">
            <el-button
              type="primary"
              :loading="uploading"
              @click="handleUpload"
              :disabled="!selectedFile"
            >
              <el-icon><upload /></el-icon>
              上传文件
            </el-button>
            <el-button @click="clearFile">清空</el-button>
          </div>
        </div>
      </div>

      <!-- 搜索区域 -->
      <div v-if="files.length > 0" class="search-section">
        <h2>文件搜索</h2>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="输入关键词进行语义搜索（支持搜索文件名和内容）"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleClearSearch"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
            <template #append>
              <el-button
                type="primary"
                :loading="searching"
                @click="handleSearch"
              >
                搜索
              </el-button>
            </template>
          </el-input>
          <div v-if="searchResults.length > 0" class="search-results-info">
            <el-tag type="success">找到 {{ searchResults.length }} 个相关文件</el-tag>
            <el-button
              type="text"
              size="small"
              @click="handleClearSearch"
            >
              清除搜索
            </el-button>
          </div>
        </div>
      </div>

      <!-- 文件列表 -->
      <div v-if="files.length > 0" class="files-section">
        <h2>{{ isSearchMode ? '搜索结果' : '已上传的文件' }}</h2>
        <el-table :data="displayFiles" style="width: 100%" stripe>
          <el-table-column prop="filename" label="文件名" width="300" />
          <el-table-column label="文件大小" width="120">
            <template #default="{ row }">
              {{ formatFileSize(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column label="文本长度" width="120">
            <template #default="{ row }">
              {{ row.text_length }} 字符
            </template>
          </el-table-column>
          <el-table-column v-if="isSearchMode" label="相似度" width="100">
            <template #default="{ row }">
              <el-tag :type="row.similarity_score > 0.7 ? 'success' : row.similarity_score > 0.5 ? 'warning' : 'info'">
                {{ (row.similarity_score * 100).toFixed(1) }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="isSearchMode" label="匹配内容" width="400" min-width="300">
            <template #default="{ row }">
              <div 
                class="match-content" 
                v-html="highlightMatchText(row.match_text, searchQuery)"
                :title="row.match_text"
              ></div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="!row.has_text" type="warning" size="small">无文本</el-tag>
              <el-tag v-else-if="row.has_summary" type="success" size="small">已总结</el-tag>
              <el-tag v-else type="info" size="small">未总结</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="320">
            <template #default="{ row }">
              <el-button
                type="success"
                size="small"
                @click="viewPDF(row.id)"
              >
                <el-icon><view /></el-icon>
                查看PDF
              </el-button>
              <el-button
                type="primary"
                size="small"
                :loading="summarizing[row.id]"
                :disabled="!row.has_text"
                @click="row.has_summary ? viewSummary(row.id) : handleSummarize(row.id)"
              >
                <el-icon><document /></el-icon>
                {{ row.has_summary ? '查看总结' : '生成总结' }}
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(row.id)"
                :loading="deleting[row.id]"
              >
                <el-icon><delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

    </el-card>

    <!-- 总结查看对话框 -->
    <el-dialog
      v-model="showSummaryDialog"
      :title="currentSummaryFileName || '文档总结'"
      :width="summaryDialogFullscreen ? '100%' : '75%'"
      :top="summaryDialogFullscreen ? '0' : '5vh'"
      :close-on-click-modal="false"
      :fullscreen="summaryDialogFullscreen"
      destroy-on-close
      class="summary-dialog"
    >
      <template #header>
        <div class="dialog-header">
          <span>{{ currentSummaryFileName || '文档总结' }}</span>
          <div class="dialog-header-actions">
            <el-button
              :icon="summaryDialogFullscreen ? Aim : FullScreen"
              circle
              size="small"
              @click="toggleSummaryFullscreen"
              title="全屏/退出全屏"
            />
          </div>
        </div>
      </template>
      <div class="summary-dialog-container">
        <!-- 左侧：大纲 -->
        <div class="summary-outline-wrapper">
          <div class="outline-header">
            <h3>目录</h3>
          </div>
          <div class="outline-content">
            <el-scrollbar :height="summaryDialogFullscreen ? 'calc(100vh - 120px)' : 'calc(80vh - 100px)'">
              <ul class="outline-list">
                <li
                  v-for="(item, index) in summaryOutline"
                  :key="index"
                  :class="['outline-item', `outline-level-${item.level}`]"
                  @click="scrollToHeading(item.id)"
                >
                  <span class="outline-text">{{ item.text }}</span>
                </li>
              </ul>
              <div v-if="summaryOutline.length === 0" class="outline-empty">
                暂无目录
              </div>
            </el-scrollbar>
          </div>
        </div>
        
        <!-- 右侧：总结内容 -->
        <div class="summary-content-wrapper">
          <div 
            class="summary-content" 
            id="summary-content"
            v-html="formatSummary(getSummaryContent())"
          ></div>
          <div v-if="getSummaryTokenUsed()" class="summary-meta">
            <el-tag type="info">使用Token数: {{ getSummaryTokenUsed() }}</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- PDF查看对话框 -->
    <el-dialog
      v-model="showPDFDialog"
      :title="currentPDFName"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="pdf-viewer-container">
        <iframe
          v-if="pdfViewUrl"
          :src="pdfViewUrl"
          class="pdf-viewer"
          frameborder="0"
        ></iframe>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled,
  Upload,
  Search,
  Document,
  Delete,
  View,
  FullScreen,
  Aim
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { uploadPDF, getFiles, summarizePDF, deleteFile, getFileDetail } from '../api/upload'
import { searchPDFs } from '../api/search'

const uploadRef = ref(null)
const fileList = ref([])
const selectedFile = ref(null)
const uploading = ref(false)
const files = ref([])
const currentSummary = ref(null)
const summarizing = reactive({})
const deleting = reactive({})
const showPDFDialog = ref(false)
const pdfViewUrl = ref('')
const currentPDFName = ref('')

// 总结对话框相关
const showSummaryDialog = ref(false)
const currentSummaryFileName = ref('')
const summaryOutline = ref([])
const summaryDialogFullscreen = ref(false)

// 搜索相关
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref([])
const isSearchMode = computed(() => searchResults.value.length > 0)

// 计算显示的文件列表（搜索模式显示搜索结果，否则显示所有文件）
const displayFiles = computed(() => {
  if (isSearchMode.value) {
    return searchResults.value
  }
  return files.value
})

// 加载文件列表
const loadFiles = async () => {
  try {
    const response = await getFiles(0, 100)
    if (response.success) {
      files.value = response.data.files
    }
  } catch (error) {
    ElMessage.error('加载文件列表失败: ' + error.message)
  }
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 清空文件
const clearFile = () => {
  selectedFile.value = null
  fileList.value = []
  uploadRef.value?.clearFiles()
}

// 上传文件
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  try {
    const response = await uploadPDF(selectedFile.value)
    if (response.success) {
      ElMessage.success('文件上传成功')
      clearFile()
      await loadFiles()
    }
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

// 生成总结
const handleSummarize = async (fileId) => {
  summarizing[fileId] = true
  try {
    ElMessage.info('正在生成总结，请稍候...')
    const response = await summarizePDF(fileId)
    if (response.success) {
      currentSummary.value = response.data
      // 获取文件名
      const file = displayFiles.value.find(f => f.id === fileId)
      currentSummaryFileName.value = file ? file.filename : '文档总结'
      // 生成大纲
      generateOutline()
      // 打开对话框
      showSummaryDialog.value = true
      ElMessage.success('总结生成成功')
      await loadFiles() // 刷新列表，更新状态
    }
  } catch (error) {
    ElMessage.error('生成总结失败: ' + error.message)
  } finally {
    summarizing[fileId] = false
  }
}

// 查看总结
const viewSummary = async (fileId) => {
  try {
    const response = await getFileDetail(fileId)
    if (response.success && response.data.summary) {
      // getFileDetail返回的格式是 { data: { summary: { content: ..., token_used: ... } } }
      // 我们需要将整个data对象赋值，这样summary字段就是包含content的对象
      currentSummary.value = {
        summary: response.data.summary
      }
      // 获取文件名
      const file = displayFiles.value.find(f => f.id === fileId)
      currentSummaryFileName.value = file ? file.filename : '文档总结'
      // 生成大纲
      generateOutline()
      // 打开对话框
      showSummaryDialog.value = true
    } else {
      ElMessage.info('该文件还没有生成总结')
      currentSummary.value = null
    }
  } catch (error) {
    ElMessage.error('获取总结失败: ' + error.message)
  }
}

// 删除文件
const handleDelete = async (fileId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个文件吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting[fileId] = true
    const response = await deleteFile(fileId)
    if (response.success) {
      ElMessage.success('删除成功')
      if (currentSummary.value && files.value.find(f => f.id === fileId)) {
        currentSummary.value = null
        showSummaryDialog.value = false
      }
      await loadFiles()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  } finally {
    deleting[fileId] = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取总结内容（兼容两种数据结构）
const getSummaryContent = () => {
  if (!currentSummary.value) return ''
  // 如果summary是字符串（来自summarizePDF）
  if (typeof currentSummary.value.summary === 'string') {
    return currentSummary.value.summary
  }
  // 如果summary是对象，包含content字段（来自getFileDetail）
  if (currentSummary.value.summary && currentSummary.value.summary.content) {
    return currentSummary.value.summary.content
  }
  // 兼容直接是content字段的情况
  if (currentSummary.value.content) {
    return currentSummary.value.content
  }
  return ''
}

// 获取Token使用数
const getSummaryTokenUsed = () => {
  if (!currentSummary.value) return null
  // 如果summary是对象，包含token_used字段
  if (currentSummary.value.summary && typeof currentSummary.value.summary === 'object') {
    return currentSummary.value.summary.token_used
  }
  // 直接是token_used字段
  return currentSummary.value.token_used || null
}

// 语义搜索
const handleSearch = async () => {
  if (!searchQuery.value || !searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  try {
    const response = await searchPDFs(searchQuery.value.trim(), 20, 0.3)
    if (response.success) {
      searchResults.value = response.data.results
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到相关文件，请尝试其他关键词')
      } else {
        ElMessage.success(`找到 ${searchResults.value.length} 个相关文件`)
      }
    }
  } catch (error) {
    ElMessage.error('搜索失败: ' + error.message)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// 清除搜索
const handleClearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

// 高亮匹配文本
const highlightMatchText = (text, query) => {
  if (!text || !query) {
    return escapeHtml(text || '')
  }
  
  // 转义HTML，防止XSS攻击
  const escapedText = escapeHtml(text)
  const escapedQuery = escapeHtml(query.trim())
  
  if (!escapedQuery) {
    return escapedText
  }
  
  let highlightedText = escapedText
  
  // 首先高亮完整的查询词（优先级最高，使用更醒目的样式）
  const fullQueryRegex = new RegExp(`(${escapeRegex(escapedQuery)})`, 'gi')
  highlightedText = highlightedText.replace(fullQueryRegex, (match) => {
    return `<mark class="highlight-match-full">${match}</mark>`
  })
  
  // 如果查询词包含多个关键词（用空格分隔），也高亮单个关键词
  // 但只高亮不在完整查询词高亮内的部分
  const keywords = escapedQuery.split(/\s+/).filter(k => k.length > 1)
  
  if (keywords.length > 0) {
    // 创建一个临时标记来避免重复高亮
    const tempMarker = '___TEMP_MARKER___'
    highlightedText = highlightedText.replace(/<mark class="highlight-match-full">([^<]*)<\/mark>/gi, 
      (match, content) => `${tempMarker}${content}${tempMarker}`)
    
    // 高亮关键词
    keywords.forEach(keyword => {
      const keywordRegex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
      highlightedText = highlightedText.replace(keywordRegex, (match, p1, offset) => {
        // 检查是否在临时标记内（即已被完整查询词高亮）
        const beforeText = highlightedText.substring(0, offset)
        const lastMarkerStart = beforeText.lastIndexOf(tempMarker)
        const lastMarkerEnd = beforeText.lastIndexOf(tempMarker, offset + match.length)
        
        if (lastMarkerStart !== -1 && lastMarkerEnd > lastMarkerStart) {
          // 在标记内，不处理
          return match
        }
        
        // 检查是否已经在mark标签内
        const beforeMatch = highlightedText.substring(0, offset)
        const lastMarkStart = beforeMatch.lastIndexOf('<mark')
        const lastMarkEnd = beforeMatch.lastIndexOf('</mark>')
        
        if (lastMarkStart > lastMarkEnd) {
          // 已经在mark标签内
          return match
        }
        
        return `<mark class="highlight-match">${match}</mark>`
      })
    })
    
    // 恢复完整查询词的高亮
    highlightedText = highlightedText.replace(new RegExp(`${tempMarker}([^${tempMarker}]*)${tempMarker}`, 'g'),
      (match, content) => `<mark class="highlight-match-full">${content}</mark>`)
  }
  
  return highlightedText
}

// 转义HTML
const escapeHtml = (text) => {
  if (!text) return ''
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 转义正则表达式特殊字符
const escapeRegex = (str) => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 查看PDF文件
const viewPDF = (fileId) => {
  // 从显示的文件列表中查找（可能是搜索结果或全部文件）
  const file = displayFiles.value.find(f => f.id === fileId)
  if (!file) return
  
  currentPDFName.value = file.filename
  // 构建PDF查看URL，通过URL参数传递token（因为iframe无法设置Authorization header）
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  pdfViewUrl.value = `/api/files/${fileId}/view`
  
  if (token) {
    pdfViewUrl.value += `?token=${encodeURIComponent(token)}`
  }
  
  showPDFDialog.value = true
}

// 格式化总结内容（Markdown转HTML）
const formatSummary = (text) => {
  if (!text) return ''
  try {
    // 使用marked将Markdown转换为HTML
    const html = marked.parse(text, {
      breaks: true, // 将单个换行符转换为<br>
      gfm: true // 启用GitHub风格的Markdown
    })
    
    // 为标题添加ID，用于大纲跳转
    return addHeadingIds(html)
  } catch (error) {
    console.error('Markdown解析失败:', error)
    // 如果解析失败，回退到简单处理
    return text.replace(/\n/g, '<br>')
  }
}

// 为HTML中的标题添加ID
const addHeadingIds = (html) => {
  if (!html) return ''
  
  // 匹配h1-h6标签，并添加ID
  return html.replace(/<h([1-6])>(.*?)<\/h[1-6]>/gi, (match, level, content) => {
    // 提取纯文本作为ID（移除HTML标签）
    const text = content.replace(/<[^>]+>/g, '').trim()
    // 生成ID：将文本转换为URL友好的格式
    const id = 'heading-' + text
      .toLowerCase()
      .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50) // 限制长度
    
    return `<h${level} id="${id}">${content}</h${level}>`
  })
}

// 从Markdown内容中提取大纲
const generateOutline = () => {
  const content = getSummaryContent()
  if (!content) {
    summaryOutline.value = []
    return
  }
  
  // 使用正则表达式匹配Markdown标题
  const headingRegex = /^(#{1,6})\s+(.+)$/gm
  const outline = []
  let match
  
  while ((match = headingRegex.exec(content)) !== null) {
    const level = match[1].length // #的数量就是级别
    const text = match[2].trim()
    
    // 生成ID（与addHeadingIds中的逻辑一致）
    const id = 'heading-' + text
      .toLowerCase()
      .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50)
    
    outline.push({
      level,
      text,
      id
    })
  }
  
  summaryOutline.value = outline
  
  // 如果对话框已打开，等待DOM更新后处理
  if (showSummaryDialog.value) {
    setTimeout(() => {
      // 确保标题ID已添加到DOM中
      outline.forEach(item => {
        const element = document.getElementById(item.id)
        if (!element) {
          // 如果找不到，尝试在格式化后的HTML中查找
          const contentElement = document.getElementById('summary-content')
          if (contentElement) {
            const headings = contentElement.querySelectorAll('h1, h2, h3, h4, h5, h6')
            headings.forEach((heading, index) => {
              if (heading.textContent.trim() === item.text && !heading.id) {
                heading.id = item.id
              }
            })
          }
        }
      })
    }, 100)
  }
}

// 点击大纲项，滚动到对应标题
const scrollToHeading = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // 高亮一下
    element.style.transition = 'background-color 0.3s'
    element.style.backgroundColor = '#fff3cd'
    setTimeout(() => {
      element.style.backgroundColor = ''
    }, 2000)
  }
}

// 切换全屏
const toggleSummaryFullscreen = () => {
  summaryDialogFullscreen.value = !summaryDialogFullscreen.value
}

// 监听对话框打开，确保大纲正确生成
watch(showSummaryDialog, async (newVal) => {
  if (newVal) {
    // 等待DOM更新
    await nextTick()
    // 重新生成大纲（确保标题ID已添加到DOM）
    generateOutline()
    // 再次等待，确保所有标题ID都已添加
    setTimeout(() => {
      // 验证并修复标题ID
      summaryOutline.value.forEach(item => {
        const element = document.getElementById(item.id)
        if (!element) {
          // 如果找不到，尝试在格式化后的HTML中查找
          const contentElement = document.getElementById('summary-content')
          if (contentElement) {
            const headings = contentElement.querySelectorAll('h1, h2, h3, h4, h5, h6')
            headings.forEach((heading) => {
              if (heading.textContent.trim() === item.text && !heading.id) {
                heading.id = item.id
              }
            })
          }
        }
      })
    }, 200)
  } else {
    // 对话框关闭时，重置全屏状态
    summaryDialogFullscreen.value = false
  }
})

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.home {
  width: 100%;
}

.main-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
}

.upload-section {
  margin-bottom: 40px;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px;
}

.file-info {
  margin-top: 20px;
}

.action-buttons {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.files-section {
  margin-top: 40px;
}

.files-section h2 {
  margin-bottom: 20px;
  color: #333;
}

.summary-section {
  margin-top: 40px;
}

.summary-section h2 {
  margin-bottom: 20px;
  color: #333;
}

.summary-card {
  background: #f8f9fa;
}

.summary-content {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  word-wrap: break-word;
}

/* Markdown样式 */
.summary-content :deep(h1) {
  font-size: 24px;
  font-weight: bold;
  margin: 20px 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
  color: #2c3e50;
}

.summary-content :deep(h2) {
  font-size: 20px;
  font-weight: bold;
  margin: 18px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
  color: #34495e;
}

.summary-content :deep(h3) {
  font-size: 18px;
  font-weight: bold;
  margin: 15px 0 10px 0;
  color: #34495e;
}

.summary-content :deep(h4) {
  font-size: 16px;
  font-weight: bold;
  margin: 12px 0 8px 0;
  color: #34495e;
}

.summary-content :deep(p) {
  margin: 10px 0;
  line-height: 1.8;
}

.summary-content :deep(ul),
.summary-content :deep(ol) {
  margin: 10px 0;
  padding-left: 30px;
}

.summary-content :deep(li) {
  margin: 6px 0;
  line-height: 1.8;
}

.summary-content :deep(strong) {
  font-weight: bold;
  color: #2c3e50;
}

.summary-content :deep(em) {
  font-style: italic;
  color: #555;
}

.summary-content :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e83e8c;
}

.summary-content :deep(pre) {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
  margin: 15px 0;
}

.summary-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: #333;
}

.summary-content :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding: 10px 15px;
  margin: 15px 0;
  color: #666;
  background-color: #f9f9f9;
}

.summary-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
}

.summary-content :deep(th),
.summary-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.summary-content :deep(th) {
  background-color: #f5f5f5;
  font-weight: bold;
}

.summary-content :deep(hr) {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 20px 0;
}

.summary-meta {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.pdf-viewer-container {
  width: 100%;
  height: 80vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f5f5;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.search-section {
  margin-bottom: 20px;
}

.search-section h2 {
  margin-bottom: 15px;
  font-size: 18px;
  color: #303133;
}

.search-box {
  margin-bottom: 10px;
}

.search-results-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.match-content {
  max-width: 100%;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
  /* 限制最大高度，超出显示省略号 */
  max-height: 4.8em; /* 约3行 */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  padding: 4px 0;
  cursor: pointer;
  transition: max-height 0.3s ease;
}

.match-content:hover {
  max-height: none;
  -webkit-line-clamp: unset;
  line-clamp: unset;
  overflow: visible;
  background-color: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 高亮样式 */
.match-content :deep(.highlight-match) {
  background-color: #fff3cd;
  color: #856404;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 500;
}

.match-content :deep(.highlight-match-full) {
  background-color: #ffc107;
  color: #000;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 总结对话框样式 */
.summary-dialog-container {
  display: flex;
  gap: 20px;
  min-height: 70vh;
}

.summary-outline-wrapper {
  width: 280px;
  flex-shrink: 0;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  border-right: 1px solid #e0e0e0;
}

.summary-content-wrapper {
  flex: 1;
  min-width: 0;
  padding-left: 20px;
}

.outline-header {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.outline-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}


.outline-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.outline-item {
  padding: 8px 12px;
  margin: 4px 0;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.outline-item:hover {
  background-color: #e6f7ff;
  border-left-color: #409eff;
  transform: translateX(3px);
}

.outline-level-1 {
  font-weight: 600;
  font-size: 15px;
  color: #2c3e50;
  padding-left: 12px;
}

.outline-level-2 {
  font-weight: 500;
  font-size: 14px;
  color: #34495e;
  padding-left: 24px;
}

.outline-level-3 {
  font-size: 13px;
  color: #555;
  padding-left: 36px;
}

.outline-level-4 {
  font-size: 12px;
  color: #666;
  padding-left: 48px;
}

.outline-level-5,
.outline-level-6 {
  font-size: 12px;
  color: #777;
  padding-left: 60px;
}

.outline-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.outline-empty {
  text-align: center;
  color: #909399;
  padding: 40px 20px;
  font-size: 14px;
}

/* 总结内容区域样式调整 */
.summary-dialog .summary-content {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  word-wrap: break-word;
  overflow-y: auto;
  padding-right: 10px;
  max-height: calc(80vh - 150px);
}

/* 全屏模式下的内容高度 */
.summary-dialog.is-fullscreen .summary-content {
  max-height: calc(100vh - 180px);
}

/* 对话框头部样式 */
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-header-actions {
  display: flex;
  gap: 8px;
}

/* 为标题添加滚动锚点样式 */
.summary-content :deep(h1),
.summary-content :deep(h2),
.summary-content :deep(h3),
.summary-content :deep(h4),
.summary-content :deep(h5),
.summary-content :deep(h6) {
  scroll-margin-top: 20px;
  position: relative;
}

.summary-dialog .summary-meta {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}
</style>

