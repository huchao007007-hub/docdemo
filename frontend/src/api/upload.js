import api from './index'

// 上传PDF文件
export const uploadPDF = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取文件列表
export const getFiles = (skip = 0, limit = 10) => {
  return api.get('/files', {
    params: { skip, limit }
  })
}

// 获取文件详情
export const getFileDetail = (fileId) => {
  return api.get(`/files/${fileId}`)
}

// 生成总结
export const summarizePDF = (fileId) => {
  return api.post(`/summarize/${fileId}`)
}

// 删除文件
export const deleteFile = (fileId) => {
  return api.delete(`/files/${fileId}`)
}

