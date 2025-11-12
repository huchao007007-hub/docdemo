import api from './index'

/**
 * 语义搜索PDF文件
 * @param {string} query - 搜索查询文本
 * @param {number} limit - 返回结果数量
 * @param {number} scoreThreshold - 相似度阈值
 * @returns {Promise}
 */
export function searchPDFs(query, limit = 10, scoreThreshold = 0.5) {
  return api.get('/search', {
    params: {
      q: query,
      limit,
      score_threshold: scoreThreshold
    }
  })
}

