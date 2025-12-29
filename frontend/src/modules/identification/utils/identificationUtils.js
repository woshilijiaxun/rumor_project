/**
 * 识别计算模块的工具函数
 */

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 验证文件类型
 * @param {File} file - 文件对象
 * @param {string[]} allowedTypes - 允许的文件类型
 * @returns {boolean} 是否有效
 */
export function validateFileType(file, allowedTypes = ['csv', 'xlsx', 'json', 'txt']) {
  const fileName = file.name.toLowerCase()
  return allowedTypes.some(type => fileName.endsWith('.' + type))
}

/**
 * 验证文件大小
 * @param {File} file - 文件对象
 * @param {number} maxSizeMB - 最大文件大小（MB）
 * @returns {boolean} 是否有效
 */
export function validateFileSize(file, maxSizeMB = 100) {
  const maxBytes = maxSizeMB * 1024 * 1024
  return file.size <= maxBytes
}

/**
 * 解析CSV文件
 * @param {string} csvContent - CSV文件内容
 * @returns {Array} 解析后的数据
 */
export function parseCSV(csvContent) {
  const lines = csvContent.trim().split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  const data = []

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim())
    const row = {}
    headers.forEach((header, index) => {
      row[header] = values[index]
    })
    data.push(row)
  }

  return data
}

/**
 * 计算置信度统计
 * @param {Array} results - 识别结果数组
 * @returns {Object} 统计信息
 */
export function calculateConfidenceStats(results) {
  if (results.length === 0) {
    return {
      min: 0,
      max: 0,
      average: 0,
      median: 0,
      stdDev: 0
    }
  }

  const confidences = results.map(r => r.confidence || 0).sort((a, b) => a - b)
  const min = confidences[0]
  const max = confidences[confidences.length - 1]
  const average = confidences.reduce((a, b) => a + b, 0) / confidences.length
  const median = confidences[Math.floor(confidences.length / 2)]

  const variance = confidences.reduce((sum, conf) => {
    return sum + Math.pow(conf - average, 2)
  }, 0) / confidences.length
  const stdDev = Math.sqrt(variance)

  return { min, max, average, median, stdDev }
}

/**
 * 计算分类统计
 * @param {Array} results - 识别结果数组
 * @returns {Object} 分类统计
 */
export function calculateClassificationStats(results) {
  const stats = {}

  results.forEach(result => {
    const category = result.output || '未分类'
    if (!stats[category]) {
      stats[category] = {
        count: 0,
        successCount: 0,
        failureCount: 0,
        avgConfidence: 0,
        confidences: []
      }
    }

    stats[category].count++
    if (result.status === 'success') {
      stats[category].successCount++
    } else {
      stats[category].failureCount++
    }
    stats[category].confidences.push(result.confidence || 0)
  })

  // 计算平均置信度
  Object.keys(stats).forEach(category => {
    const confidences = stats[category].confidences
    stats[category].avgConfidence = confidences.length > 0
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : 0
    delete stats[category].confidences
  })

  return stats
}

/**
 * 生成识别报告
 * @param {Array} results - 识别结果数组
 * @param {Object} metadata - 元数据
 * @returns {Object} 报告对象
 */
export function generateReport(results, metadata = {}) {
  const successCount = results.filter(r => r.status === 'success').length
  const failureCount = results.filter(r => r.status === 'failure').length
  const successRate = results.length > 0 ? (successCount / results.length) * 100 : 0

  const confidenceStats = calculateConfidenceStats(results)
  const classificationStats = calculateClassificationStats(results)

  return {
    timestamp: new Date().toISOString(),
    totalCount: results.length,
    successCount,
    failureCount,
    successRate: successRate.toFixed(2),
    confidenceStats,
    classificationStats,
    metadata
  }
}

/**
 * 导出为JSON
 * @param {Array} results - 识别结果数组
 * @param {string} fileName - 文件名
 */
export function exportAsJSON(results, fileName = 'results.json') {
  const dataStr = JSON.stringify(results, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  downloadFile(dataBlob, fileName)
}

/**
 * 导出为CSV
 * @param {Array} results - 识别结果数组
 * @param {string} fileName - 文件名
 */
export function exportAsCSV(results, fileName = 'results.csv') {
  if (results.length === 0) return

  const headers = Object.keys(results[0])
  const csv = [
    headers.join(','),
    ...results.map(row =>
      headers.map(header => {
        const value = row[header]
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`
        }
        return value
      }).join(',')
    )
  ].join('\n')

  const dataBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  downloadFile(dataBlob, fileName)
}

/**
 * 下载文件
 * @param {Blob} blob - 文件内容
 * @param {string} fileName - 文件名
 */
export function downloadFile(blob, fileName) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化时间戳
 * @param {number|string} timestamp - 时间戳
 * @param {string} format - 格式字符串
 * @returns {string} 格式化后的时间
 */
export function formatTime(timestamp, format = 'YYYY-MM-DD HH:mm:ss') {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 计算处理耗时
 * @param {number} startTime - 开始时间戳
 * @param {number} endTime - 结束时间戳
 * @returns {string} 格式化的耗时
 */
export function calculateDuration(startTime, endTime) {
  const duration = endTime - startTime
  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
}

/**
 * 验证识别结果
 * @param {Object} result - 识别结果对象
 * @returns {boolean} 是否有效
 */
export function validateResult(result) {
  return (
    result &&
    typeof result === 'object' &&
    'input' in result &&
    'output' in result &&
    'confidence' in result &&
    'status' in result &&
    typeof result.confidence === 'number' &&
    result.confidence >= 0 &&
    result.confidence <= 1
  )
}

/**
 * 批量验证识别结果
 * @param {Array} results - 识别结果数组
 * @returns {Object} 验证结果
 */
export function validateResults(results) {
  const valid = []
  const invalid = []

  results.forEach((result, index) => {
    if (validateResult(result)) {
      valid.push(result)
    } else {
      invalid.push({ index, result })
    }
  })

  return { valid, invalid, isValid: invalid.length === 0 }
}

