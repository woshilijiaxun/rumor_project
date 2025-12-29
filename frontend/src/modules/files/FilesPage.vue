<template>
  <div class="files-page">
    <div class="page-header">
      <h3>文件列表</h3>
      <div class="file-actions">
        <button type="button" class="btn-upload" @click="openUpload">
          <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          上传文件
        </button>
        <button type="button" class="refresh-btn" @click="fetchFiles">刷新</button>
      </div>
    </div>

    <div v-if="filesLoading" class="loading">加载中...</div>
    <div v-if="filesError" class="error">{{ filesError }}</div>

    <!-- 搜索栏，与算法管理页面风格一致 -->
    <div class="filter-bar">
      <input
        v-model="fileSearch"
        type="text"
        placeholder="搜索文件名或类型..."
        class="search-input"
      />
    </div>

    <table v-if="!filesLoading && !filesError" class="users-table">
      <thead>
        <tr>
          <th>序号</th>
          <th>文件名</th>
          <th>类型</th>
          <th>大小</th>
          <th>上传时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(f, idx) in displayFiles" :key="f.id">
          <td>{{ (page - 1) * page_size + idx + 1 }}</td>
          <td :title="f.original_name">{{ getFileNameWithoutExt(f.original_name) }}</td>
          <td>{{ getFileExtension(f.original_name) }}</td>
          <td>{{ formatSize(f.size_bytes) }}</td>
          <td>{{ formatDate(f.created_at) }}</td>
          <td class="ops">
            <a href="javascript:void(0)" @click="previewFile(f)">预览</a>
            <a href="javascript:void(0)" @click="downloadFile(f)">下载</a>
            <a href="javascript:void(0)" @click="removeFile(f)">删除</a>
          </td>
        </tr>
        <tr v-if="files.length === 0">
          <td colspan="6" class="empty">暂无文件</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination" v-if="total > page_size">
      <button :disabled="page<=1" @click="changePage(page-1)">上一页</button>
      <span>第 {{ page }} / {{ Math.ceil(total / page_size) }} 页</span>
      <button :disabled="page>=Math.ceil(total / page_size)" @click="changePage(page+1)">下一页</button>
    </div>

    <!-- 上传文件弹窗 -->
    <div v-show="uploadVisible" class="modal-mask" @click.self="closeUpload">
      <div class="modal-container upload-modal">
        <h3 class="modal-title">上传文件</h3>
        <p class="hint">仅支持上传 .txt 和 .csv 文件，单文件上限 20MB，可同时选择多个文件。</p>

        <div class="form-row file-chooser">
          <input id="uploadFileInput" type="file" multiple @change="onFileChange" ref="fileInput" style="display:none" accept=".txt,.csv,text/plain,text/csv" />
          <button type="button" class="choose-btn" @click="chooseFile">选择文件</button>
          <template v-if="uploadFiles && uploadFiles.length">
            <span v-for="(f, idx) in uploadFiles" :key="f.name + '_' + f.size + '_' + idx" class="file-chip" :title="f.name">
              {{ f.name }}（{{ formatSize(f.size) }}）
              <button type="button" class="chip-remove" @click.stop="removeUploadFile(idx)" title="移除">×</button>
            </span>
          </template>
          <span v-else class="file-chip empty">未选择文件</span>
        </div>

        <div v-if="uploadError" class="form-error">{{ uploadError }}</div>
        <div v-if="uploadSuccess" class="form-success">{{ uploadSuccess }}</div>

        <div v-if="uploading" class="progress">
          <div class="bar" :style="{ width: uploadProgress + '%' }"></div>
          <span class="progress-text">{{ uploadProgress }}%</span>
        </div>

        <div class="actions">
          <button @click="closeUpload" :disabled="uploading">取消</button>
          <button class="primary" @click="doUpload" :disabled="uploadFiles.length === 0 || uploading">{{ uploading ? '上传中...' : '开始上传' }}</button>
        </div>
      </div>
    </div>

    <!-- 上传结果确认弹窗 -->
    <div v-if="uploadResultVisible" class="modal-mask result-mask" @click.self="confirmUploadResult">
      <div class="modal-container result-modal">
        <h3 class="modal-title">提示</h3>
        <p style="margin: 8px 0 16px; color:#333;">{{ uploadResultMessage || '文件上传成功' }}</p>
        <div class="actions">
          <button class="primary" @click="confirmUploadResult">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'FilesPage',
  data() {
    return {
      files: [], filesLoading: false, filesError: '',
      page: 1, page_size: 10, total: 0,
      fileSearch: '',
      uploadVisible: false, uploadFiles: [], uploading: false, uploadProgress: 0,
      uploadError: '', uploadSuccess: '', uploadResultVisible: false, uploadResultMessage: '',
      uploadedCount: 0, failedCount: 0
    }
  },
  computed: {
    displayFiles() {
      const kw = (this.fileSearch || '').trim().toLowerCase()
      if (!kw) return this.files
      return this.files.filter(f => {
        const name = (f.original_name || '').toLowerCase()
        const type = (f.mime_type || '').toLowerCase()
        return name.includes(kw) || type.includes(kw)
      })
    }
  },
  methods: {
    fetchFiles() {
      this.filesLoading = true
      this.filesError = ''
      const guard = setTimeout(() => {
        if (this.filesLoading) { this.filesLoading = false; this.filesError = '加载超时，请点击刷新重试' }
      }, 8000)
      axios.get('/api/uploads', { params: { page: this.page, page_size: this.page_size } })
        .then(res => {
          clearTimeout(guard)
          if (res.data?.status === 'success') {
            const d = res.data.data || {}
            this.files = Array.isArray(d.items) ? d.items : (Array.isArray(d) ? d : [])
            this.total = d.total || 0
            this.filesError = ''
          } else { this.filesError = res.data?.message || '获取文件列表失败'; this.files = [] }
          this.filesLoading = false
        })
        .catch(err => { clearTimeout(guard); this.filesError = err.response?.data?.message || err.message || '获取文件列表失败'; this.files = []; this.filesLoading = false })
    },
    changePage(p) { this.page = p; this.fetchFiles() },
    previewFile(f) {
      const token = localStorage.getItem('token') || ''
      const url = `/api/uploads/${f.id}/file?token=${encodeURIComponent(token)}`
      window.open(url, '_blank')
    },
    downloadFile(f) {
      const token = localStorage.getItem('token') || ''
      const url = `/api/uploads/${f.id}/download?token=${encodeURIComponent(token)}`
      const a = document.createElement('a')
      a.href = url
      a.download = f.original_name || 'download'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    removeFile(f) {
      if (!confirm(`确认删除文件: ${f.original_name} ?`)) return
      axios.delete(`/api/uploads/${f.id}`).then(res => {
        if (res.data?.status === 'success') this.fetchFiles()
        else alert(res.data?.message || '删除失败')
      }).catch(err => { alert(err.response?.data?.message || err.message || '删除失败') })
    },
    openUpload() { this.uploadVisible = true; this.uploadFiles = []; this.uploadError = ''; this.uploadSuccess = ''; this.uploadProgress = 0; this.uploadedCount = 0; this.failedCount = 0 },
    closeUpload() { this.uploadVisible = false },
    chooseFile() { const input = this.$refs.fileInput; if (input) input.click() },
    onFileChange(e) { 
      const files = e.target.files
      if (!files) return
      this.uploadFiles = []
      this.uploadError = ''
      this.uploadSuccess = ''
      this.uploadProgress = 0
      for (let i = 0; i < files.length; i++) {
        const f = files[i]
        if (f.size > 20 * 1024 * 1024) {
          this.uploadError = `文件 ${f.name} 大小超过 20MB，已跳过`
          continue
        }
        this.uploadFiles.push(f)
      }
    },
    removeUploadFile(idx) {
      this.uploadFiles.splice(idx, 1)
      if (this.$refs.fileInput) this.$refs.fileInput.value = ''
    },
    doUpload() {
      if (this.uploadFiles.length === 0) { this.uploadError = '请先选择文件'; return }
      this.uploadError = ''; this.uploadSuccess = ''; this.uploadedCount = 0; this.failedCount = 0
      this.uploading = true; this.uploadProgress = 0
      const totalFiles = this.uploadFiles.length
      let completedCount = 0
      const uploadPromises = this.uploadFiles.map((file, idx) => {
        return new Promise((resolve) => {
          const fd = new FormData()
          fd.append('file', file)
          axios.post('/api/upload', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (evt) => {
              if (evt.total) {
                const fileProgress = Math.round((evt.loaded / evt.total) * 100)
                const totalProgress = Math.round(((completedCount + fileProgress / 100) / totalFiles) * 100)
                this.uploadProgress = totalProgress
              }
            }
          }).then(res => {
            if (res.data?.status === 'success') {
              this.uploadedCount++
            } else {
              this.failedCount++
            }
            completedCount++
            resolve()
          }).catch(err => {
            this.failedCount++
            completedCount++
            resolve()
          })
        })
      })
      Promise.all(uploadPromises).then(() => {
        this.uploading = false
        this.uploadProgress = 100
        if (this.failedCount === 0) {
          this.uploadSuccess = `成功上传 ${this.uploadedCount} 个文件`
          this.uploadResultMessage = `成功上传 ${this.uploadedCount} 个文件`
        } else if (this.uploadedCount === 0) {
          this.uploadError = `${this.failedCount} 个文件上传失败`
          this.uploadResultMessage = `${this.failedCount} 个文件上传失败`
        } else {
          this.uploadSuccess = `成功上传 ${this.uploadedCount} 个文件，${this.failedCount} 个失败`
          this.uploadResultMessage = `成功上传 ${this.uploadedCount} 个文件，${this.failedCount} 个失败`
        }
        setTimeout(() => { this.fetchFiles() }, 500)
        this.uploadResultVisible = true
        this.uploadFiles = []; if (this.$refs.fileInput) this.$refs.fileInput.value = ''
      })
    },
    confirmUploadResult() { this.uploadResultVisible = false; this.uploadVisible = false; this.uploadError = ''; this.uploadSuccess = ''; this.uploadProgress = 0; this.uploadedCount = 0; this.failedCount = 0; if (this.files.length === 0) this.fetchFiles() },
    getFileNameWithoutExt(filename) { if (!filename) return '-'; const lastDotIndex = filename.lastIndexOf('.'); return lastDotIndex > 0 ? filename.substring(0, lastDotIndex) : filename },
    getFileExtension(filename) { if (!filename) return '-'; const lastDotIndex = filename.lastIndexOf('.'); if (lastDotIndex > 0) { const ext = filename.substring(lastDotIndex + 1).toUpperCase(); return ext || '-' } return '-' },
    formatDate(v) { if (!v) return '-'; const t = Date.parse(v); if (isNaN(t)) return v; return new Date(t).toLocaleString('zh-CN') },
    formatSize(b) { if (b == null) return '-'; const units = ['B','KB','MB','GB','TB']; let n = Number(b), i = 0; while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ } return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${units[i]}` }
  },
  mounted() { this.fetchFiles() }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h3 { margin: 0; color: #333; }
.refresh-btn { padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.refresh-btn:hover { background: #40a9ff; }
.loading, .error { text-align: left; padding: 8px 0; color: #666; }
.error { color: #d32f2f; }
.users-table { width: 100%; border-collapse: collapse; }
.users-table th, .users-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.users-table th { background: #fafafa; font-weight: 600; color: #333; }
.users-table tbody tr:hover { background: #fafafa; }
.empty { text-align: center; color: #999; padding: 40px; }
.ops a { margin-right: 10px; color: #1890ff; text-decoration: none; cursor: pointer; }
.ops a:hover { text-decoration: underline; color: #40a9ff; }
.ops a:active { color: #096dd9; }
.pagination { display: flex; align-items: center; gap: 10px; justify-content: flex-end; margin-top: 12px; }
.pagination button { padding: 6px 12px; border: 1px solid #dcdfe6; background: #fff; border-radius: 4px; cursor: pointer; }
.pagination button:disabled { opacity: .6; cursor: not-allowed; }

/* 弹窗样式（与原 Home 保持一致） */
.modal-mask { position: fixed; z-index: 4000; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-container { width: 420px; max-width: 90vw; background: #fff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.15); padding: 20px; }
.modal-title { margin: 0 0 12px; font-size: 18px; font-weight: 700; color: #333; }
.form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.form-row label { font-size: 13px; color: #666; }
.divider { height: 1px; background: #f0f0f0; margin: 12px 0; }
.form-error { color: #d93025; margin: 6px 0; }
.form-success { color: #2e7d32; margin: 6px 0; }
.actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.actions button { padding: 8px 14px; border: 1px solid #dcdfe6; background: #fff; color: #333; border-radius: 6px; cursor: pointer; }
.actions button.primary { background: #1890ff; border-color: #1890ff; color: #fff; }
.actions button:disabled { opacity: .6; cursor: not-allowed; }

/* 上传按钮（与首页统一） */
.file-actions { display: flex; align-items: center; gap: 10px; }
.btn-upload { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 8px; border: 1px solid #1677ff; color: #fff; background: linear-gradient(90deg, #1677ff 0%, #4096ff 100%); box-shadow: 0 4px 10px rgba(22, 119, 255, 0.25); cursor: pointer; font-weight: 600; font-size: 14px; transition: background .2s ease, box-shadow .2s ease, transform .08s ease; }
.btn-upload:hover { background: linear-gradient(90deg, #3b8cff 0%, #62a6ff 100%); box-shadow: 0 6px 14px rgba(22, 119, 255, 0.32); }
.btn-upload:active { transform: translateY(1px); }
.btn-upload .icon { width: 16px; height: 16px; flex: 0 0 16px; }

/* 选择文件按钮 */
.choose-btn { display:inline-block; padding:8px 14px; background:#1890ff; color:#fff; border-radius:6px; cursor:pointer; user-select:none; border:none; font-size:14px; transition:background .2s ease; }
.choose-btn:hover { background:#40a9ff; }
.choose-btn:active { background:#096dd9; }
.file-chooser { display: flex; align-items: center; gap: 10px; }
.file-chip { display: inline-flex; align-items: center; max-width: 260px; padding: 6px 10px; border-radius: 16px; background: #f5f7fa; color: #333; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; gap: 6px; }
.file-chip.empty { color: #999; background: #fafafa; border: 1px dashed #e5e7eb; }
.chip-remove { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; padding: 0; border: none; background: transparent; color: #999; cursor: pointer; font-size: 16px; line-height: 1; flex-shrink: 0; transition: color .2s ease; }
.chip-remove:hover { color: #d32f2f; }
.progress { position: relative; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; margin: 6px 0 12px; }
.progress .bar { height: 100%; background: #1890ff; width: 0; transition: width .2s ease; }
.progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 12px; color: #666; font-weight: 500; white-space: nowrap; }
/* 搜索栏样式（与算法页保持一致） */
.filter-bar { display: flex; gap: 10px; margin: 10px 0 12px; }
.search-input { padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; width: 320px; }
.search-input:focus { outline: none; border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,.15); }
</style>

