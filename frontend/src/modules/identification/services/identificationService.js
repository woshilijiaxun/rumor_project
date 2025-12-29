/**
 * 识别计算服务（方案2：algo_key 稳定键）
 */

const API_BASE_URL = '/api/identification'

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
  'Content-Type': 'application/json'
})

export const identificationService = {
  /**
   * 创建识别任务（异步）
   * @param {number} fileId
   * @param {string} algorithmKey  (algo_key)
   * @param {Object} params
   */
  async createTask(fileId, algorithmKey, params = {}) {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        file_id: fileId,
        algorithm_key: algorithmKey,
        params
      })
    })

    const data = await response.json().catch(() => null)
    if (!response.ok || data?.status !== 'success') {
      throw new Error(data?.message || `创建任务失败 (HTTP ${response.status})`)
    }
    return data
  },

  async getTask(taskId) {
    const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || data?.status !== 'success') {
      throw new Error(data?.message || `获取任务失败 (HTTP ${response.status})`)
    }
    return data
  },

  async getResult(taskId) {
    const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}/result`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || data?.status !== 'success') {
      throw new Error(data?.message || `获取结果失败 (HTTP ${response.status})`)
    }
    return data
  },

  async cancelTask(taskId) {
    const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}/cancel`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
    })
    const data = await response.json().catch(() => null)
    if (!response.ok || data?.status !== 'success') {
      throw new Error(data?.message || `取消任务失败 (HTTP ${response.status})`)
    }
    return data
  }
}
