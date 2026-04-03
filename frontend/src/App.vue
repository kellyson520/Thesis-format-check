<script setup>
import { ref, computed, onMounted } from 'vue'

// ── API Configuration (P5: Dynamic Handshake) ───────────────────────────────
const token = ref('')
const apiPort = ref('8000')
const API = computed(() => `http://127.0.0.1:${apiPort.value}`)

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  token.value = params.get('token') || ''
  apiPort.value = params.get('port') || window.location.port || '8000'
  loadRulesSummary()
})

const fetchWithAuth = (url, options = {}) => {
  const headers = {
    ...options.headers,
    'X-Token': token.value
  }
  return fetch(url, { ...options, headers })
}

// ── State ────────────────────────────────────────────────────────────────────
const activeTab = ref('check')   // 'check' | 'rules' | 'logs' | 'settings'
const isDragging = ref(false)
const loading = ref(false)
const progress = ref(0)
const validationDone = ref(false)
const fileName = ref('')
const uploadedFile = ref(null)
const issues = ref([])
const checkedAt = ref('')

const rulesLoading = ref(false)
const rulesSummary = ref(null)
const libraries = ref([])
const currentLibrary = ref('')
const logsLoading = ref(false)
const logs = ref([])
const logLevelFilter = ref('')

const exporting = ref(false)
const fixing = ref(false)
const isEditingRules = ref(false)
const fullRules = ref(null)
const rulesSubTab = ref('general')

// ── Settings ─────────────────────────────────────────────────────────────────
const systemSettings = ref(null)
const isSettingsLoading = ref(false)
const isCheckingUpdate = ref(false)
const updateInfo = ref(null)

// ── Computed ─────────────────────────────────────────────────────────────────
const errorCount = computed(() => issues.value.filter(i => i.type === 'Error').length)
const warnCount  = computed(() => issues.value.filter(i => i.type === 'Warn').length)

const filteredLogs = computed(() => {
  if (!logLevelFilter.value) return logs.value
  return logs.value.filter(l => l.level === logLevelFilter.value)
})

// ── File Check ────────────────────────────────────────────────────────────────
const handleDrop = async (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file?.name.endsWith('.docx')) await uploadFile(file)
  else alert('请上传 .docx 格式的论文文件')
}

const onFileChange = async (e) => {
  const file = e.target.files[0]
  if (file) await uploadFile(file)
}

const uploadFile = async (file) => {
  uploadedFile.value = file
  fileName.value = file.name
  loading.value = true
  progress.value = 0
  issues.value = []
  validationDone.value = false

  const fd = new FormData()
  fd.append('file', file)

  try {
    // P5: 使用流式接口处理超长文档
    const response = await fetchWithAuth(`${API.value}/api/check/stream`, { 
      method: 'POST', 
      body: fd 
    })

    if (!response.ok) throw new Error(await response.text())

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() // 保留未完整的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const rawJson = line.replace('data: ', '')
        try {
          const event = JSON.parse(rawJson)
          
          if (event.event_type === 'progress') {
            progress.value = event.progress
            if (event.issues && event.issues.length) {
              issues.value.push(...event.issues)
            }
          } else if (event.event_type === 'section_issues') {
            issues.value.push(...event.issues)
          } else if (event.event_type === 'done') {
            validationDone.value = true
            checkedAt.value = new Date().toLocaleString()
          } else if (event.type === 'error') {
            alert('校验中断: ' + event.message)
          }
        } catch (e) {
          console.error('JSON解析失败:', rawJson, e)
        }
      }
    }
  } catch (err) {
    alert('校验失败: ' + err.message)
    console.error(err)
  } finally {
    loading.value = false
    progress.value = 100
  }
}

const reCheck = async () => {
  if (!uploadedFile.value || loading.value) return
  await uploadFile(uploadedFile.value)
}

// ── Copy Report ────────────────────────────────────────────────────────────────
const copyReport = () => {
  const lines = [`论文格式校验报告 — ${fileName.value}`, `时间: ${checkedAt.value}`, `共发现异常: ${issues.value.length} 条`, '']
  issues.value.forEach((iss, idx) => {
    lines.push(`[${idx + 1}] [${iss.type}] 段落 #${iss.id}`)
    lines.push(`  片段: "${iss.context}"`)
    lines.push(`  问题: ${iss.message}`)
    lines.push('')
  })
  navigator.clipboard.writeText(lines.join('\n'))
    .then(() => showToast('已复制到剪贴板！'))
    .catch(() => alert('复制失败，请手动选取'))
}

// ── Export Annotated Docx ─────────────────────────────────────────────────────
const exportAnnotated = async () => {
  if (!uploadedFile.value || !issues.value.length) return
  exporting.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadedFile.value)
    fd.append('issues_json', JSON.stringify(issues.value))
    const res = await fetchWithAuth(`${API.value}/api/export/annotated`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName.value.replace('.docx', '_校验批注.docx')
    a.click()
    URL.revokeObjectURL(url)
    showToast('批注文件已导出！')
  } catch (err) {
    alert(`导出失败：${err.message}`)
  } finally {
    exporting.value = false
  }
}

// ── Auto-Fix Docx ─────────────────────────────────────────────────────────────
const fixDocument = async () => {
  if (!uploadedFile.value || !issues.value.length) return
  fixing.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadedFile.value)
    
    // Auto-fix does not need issues array because backend fixer parses and fixes everything based on rules
    const res = await fetchWithAuth(`${API.value}/api/fix`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName.value.replace('.docx', '_格式已修复.docx')
    a.click()
    URL.revokeObjectURL(url)
    showToast('论文格式已一键修复完成并下载！')
  } catch (err) {
    alert(`修复失败：${err.message}`)
  } finally {
    fixing.value = false
  }
}

// ── Rules Tab ─────────────────────────────────────────────────────────────────
const toggleEditRules = async () => {
  if (!isEditingRules.value) {
    rulesLoading.value = true
    try {
      const res = await fetchWithAuth(`${API.value}/api/rules/full_json`)
      fullRules.value = await res.json()
      // Ensure nested keys exist for reactive binding
      if (!fullRules.value.validators) fullRules.value.validators = { check_font: true, check_spacing: true, check_hierarchy: true, check_gb7714: true }
      if (!fullRules.value.page_setup) fullRules.value.page_setup = { top_margin_cm: 2.54, bottom_margin_cm: 2.54, left_margin_cm: 3.18, right_margin_cm: 3.18 }
      if (!fullRules.value.pagination) fullRules.value.pagination = { enabled: true, widow_control: true, keep_with_next_styles: ["Heading 1", "Heading 2", "Heading 3", "标题 1", "标题 2", "标题 3"] }
      if (fullRules.value.pagination.keep_with_next_styles) {
        fullRules.value.pagination.keep_with_next_styles_str = fullRules.value.pagination.keep_with_next_styles.join(', ')
      }
      isEditingRules.value = true
      rulesSubTab.value = 'general'
    } catch (err) {
      alert("加载完整规则失败：" + err.message)
    } finally {
      rulesLoading.value = false
    }
  } else {
    isEditingRules.value = false
  }
}

const saveRules = async () => {
  try {
    const res = await fetchWithAuth(`${API.value}/api/rules/save_json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fullRules.value)
    })
    if (!res.ok) throw new Error(await res.text())
    showToast("规则已保存至后端并热重载！")
    isEditingRules.value = false
    await loadRulesSummary()
  } catch(err) {
    alert("保存失败：" + err.message)
  }
}

const loadRulesSummary = async () => {
  rulesLoading.value = true
  try {
    const res = await fetchWithAuth(`${API.value}/api/rules/summary`)
    rulesSummary.value = await res.json()
    await loadLibraries()
  } finally {
    rulesLoading.value = false
  }
}

const loadLibraries = async () => {
  try {
    const res = await fetchWithAuth(`${API.value}/api/rules/libraries`)
    const data = await res.json()
    libraries.value = data.libraries || []
    currentLibrary.value = data.current || ''
  } catch(e) { console.error("加载规则库失败", e) }
}

const switchLibrary = async () => {
  if (!currentLibrary.value) return
  rulesLoading.value = true
  try {
    const res = await fetchWithAuth(`${API.value}/api/rules/switch?filename=${currentLibrary.value}`, { method: 'POST' })
    const data = await res.json()
    showToast(data.message)
    await loadRulesSummary()
  } catch(e) { alert("切换失败: " + e.message) }
  finally { rulesLoading.value = false }
}

const downloadRules = async (fmt) => {
  const res = await fetchWithAuth(`${API.value}/api/rules/export/${fmt}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `rules_export.${fmt}`
  a.click()
  URL.revokeObjectURL(url)
  showToast(`规则已导出为 ${fmt.toUpperCase()}`)
}

const importRules = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await fetchWithAuth(`${API.value}/api/rules/import`, { method: 'POST', body: fd })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '导入失败')
    showToast(data.message || '规则导入成功')
    await loadRulesSummary()
  } catch (err) {
    alert(`规则导入失败：${err.message}`)
  }
}

const reloadRules = async () => {
  const res = await fetchWithAuth(`${API.value}/api/rules/reload`, { method: 'POST' })
  const data = await res.json()
  showToast(data.message)
  await loadRulesSummary()
}

// ── Logs Tab ──────────────────────────────────────────────────────────────────
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const url = logLevelFilter.value
      ? `${API.value}/api/logs?limit=200&level=${logLevelFilter.value}`
      : `${API.value}/api/logs?limit=200`
    const res = await fetchWithAuth(url)
    const data = await res.json()
    logs.value = (data.logs || []).reverse()
  } finally {
    logsLoading.value = false
  }
}

const clearLogs = async () => {
  if (!confirm('确认清空所有日志记录？')) return
  await fetchWithAuth(`${API.value}/api/logs`, { method: 'DELETE' })
  logs.value = []
  showToast('日志已清空')
}

// ── Tab switch side-effects ───────────────────────────────────────────────────
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'rules' && !rulesSummary.value) loadRulesSummary()
  if (tab === 'logs') loadLogs()
  if (tab === 'settings') loadSystemSettings()
}

// ── Toast Notification ────────────────────────────────────────────────────────
const toast = ref(null)
const showToast = (msg) => {
  toast.value = msg
  setTimeout(() => { toast.value = null }, 2800)
}

// ── Settings API ─────────────────────────────────────────────────────────────
const loadSystemSettings = async () => {
  isSettingsLoading.value = true
  try {
    const res = await fetchWithAuth(`${API.value}/api/settings`)
    systemSettings.value = await res.json()
  } catch (err) {
    console.error("加载设置失败", err)
  } finally {
    isSettingsLoading.value = false
  }
}

const togglePlugin = async (plugin) => {
  try {
    const res = await fetchWithAuth(`${API.value}/api/settings/plugin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: plugin.id, enabled: !plugin.enabled })
    })
    if (!res.ok) throw new Error(await res.text())
    plugin.enabled = !plugin.enabled
    showToast(`${plugin.name} 状态已更新`)
  } catch (err) {
    alert("更新失败: " + err.message)
  }
}

const clearSystemCache = async () => {
  if (!confirm('确认清理所有系统缓存和旧日志？')) return
  try {
    const res = await fetchWithAuth(`${API.value}/api/settings/clear_cache`, { method: 'POST' })
    const data = await res.json()
    showToast(`清理成功: 已删除 ${data.deleted_items} 个项`)
    await loadSystemSettings()
  } catch (err) {
    alert("清理失败: " + err.message)
  }
}

const checkUpdate = async () => {
  isCheckingUpdate.value = true
  updateInfo.value = null
  try {
    const res = await fetchWithAuth(`${API.value}/api/settings/check_update`)
    updateInfo.value = await res.json()
  } catch (err) {
    alert("检查更新失败")
  } finally {
    isCheckingUpdate.value = false
  }
}

const openSettings = () => {
  switchTab('settings')
}

// ── Utility ────────────────────────────────────────────────────────────────────
const levelColor = (level) => {
  if (level === 'ERROR') return '#f87171'
  if (level === 'WARNING') return '#fbbf24'
  if (level === 'INFO') return '#60a5fa'
  return '#94a3b8'
}
</script>

<template>
  <div class="app-shell">
    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>

    <!-- Sidebar Navigation -->
    <nav class="sidebar">
      <div class="brand">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#a78bfa"/></linearGradient></defs>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <span class="brand-name">论文校验</span>
      </div>
      <button class="nav-item" :class="{ active: activeTab === 'check' }" @click="switchTab('check')">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
        格式校验
      </button>
      <button class="nav-item" :class="{ active: activeTab === 'rules' }" @click="switchTab('rules')">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path><path d="M4.93 4.93a10 10 0 0 0 0 14.14"></path></svg>
        规则管理
      </button>
      <button class="nav-item" :class="{ active: activeTab === 'logs' }" @click="switchTab('logs')">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><polyline points="14 2 14 8 20 8"></polyline></svg>
        系统日志
      </button>

      <div style="flex:1"></div>

      <button class="nav-item" :class="{ active: activeTab === 'settings' }" @click="switchTab('settings')" style="margin-top:auto">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        系统设置
      </button>
    </nav>

    <!-- Main Content Area -->
    <main class="main-content">

      <!-- ── CHECK TAB ───────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'check'" class="tab-panel">
        <div class="panel-header">
          <h1 class="panel-title">论文格式深度校验</h1>
          <p class="panel-sub">拖拽或点击上传您的 .docx 论文文件，引擎将逐段扫描并生成精准报告</p>
        </div>

        <!-- Drop Zone -->
        <div class="dropzone" :class="{ active: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop">
          <input type="file" id="file-input" @change="onFileChange" accept=".docx" hidden />
          <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="upload-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          <label for="file-input" class="upload-btn">点击选择文件</label>
          <span class="drop-hint">或将 .docx 文件拖拽至此处</span>
          <div v-if="fileName" class="file-badge">📄 {{ fileName }}</div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loader-row">
          <div class="spinner"></div>
          <div class="progress-box">
            <div class="progress-info">
              <span class="pulse-text">校验引擎运行中... ({{ progress }}%)</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- Results Panel -->
        <div v-if="!loading && validationDone" class="results fade-in">
          <!-- Stats Row -->
          <div class="stats-row">
            <div class="stat-card">
              <span class="stat-num" style="color:#f87171">{{ errorCount }}</span>
              <span class="stat-label">严重错误</span>
            </div>
            <div class="stat-card">
              <span class="stat-num" style="color:#fbbf24">{{ warnCount }}</span>
              <span class="stat-label">警告提示</span>
            </div>
            <div class="stat-card">
              <span class="stat-num" style="color:#60a5fa">{{ issues.length }}</span>
              <span class="stat-label">问题总计</span>
            </div>
            <div class="stat-card">
              <span class="stat-num" style="color:#4ade80; font-size:0.9rem">{{ checkedAt ? checkedAt.split('T')[1].split('.')[0] : '--' }}</span>
              <span class="stat-label">校验时间</span>
            </div>
          </div>

          <!-- Action Row -->
          <div class="action-row">
            <button class="btn btn-ghost" @click="reCheck" :disabled="loading">
              🔄 重新检测
            </button>
            <button class="btn btn-ghost" @click="copyReport">
              📋 复制报告文本
            </button>
            <button class="btn btn-primary" :disabled="exporting || !issues.length" @click="exportAnnotated">
              <span v-if="exporting">导出中...</span>
              <span v-else>📥 导出批注 Docx</span>
            </button>
            <button class="btn btn-primary" style="background: linear-gradient(135deg, #10b981, #047857);" :disabled="fixing || !issues.length" @click="fixDocument">
              <span v-if="fixing">修复中...</span>
              <span v-else>✨ 一键排版修复 (Auto-Fix)</span>
            </button>
          </div>

          <!-- Issue Cards -->
          <div v-if="issues.length" class="issues-list">
            <div v-for="(issue, idx) in issues" :key="idx"
              class="issue-card" :class="issue.type === 'Error' ? 'is-error' : 'is-warn'">
              <div class="card-header">
                <span class="badge" :class="issue.type === 'Error' ? 'badge-error' : 'badge-warn'">{{ issue.type }}</span>
                <span class="para-id">¶ 段落 #{{ issue.id }}</span>
              </div>
              <p class="context">"{{ issue.context }}"</p>
              <p class="msg">{{ issue.message }}</p>
            </div>
          </div>
          <div v-else class="success-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <p>完美！未检测到任何格式问题</p>
          </div>
        </div>
      </div>

      <!-- ── RULES TAB ───────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'rules'" class="tab-panel">
        <div class="panel-header">
          <h1 class="panel-title">规则管理中心</h1>
          <p class="panel-sub">查看当前生效规则、导入自定义规则文件、导出备份</p>
        </div>

        <div v-if="rulesLoading" class="loader-row">
          <div class="spinner"></div> <span class="pulse-text">加载规则摘要...</span>
        </div>

        <div v-if="rulesSummary && !isEditingRules" class="rules-grid fade-in">
          <div class="rule-card">
            <h3>中文正文字体</h3>
            <p class="rule-val">{{ rulesSummary.default_font_east_asia }}</p>
          </div>
          <div class="rule-card">
            <h3>英文字体</h3>
            <p class="rule-val">{{ rulesSummary.default_font_ascii || '未设置' }}</p>
          </div>
          <div class="rule-card">
            <h3>缺省字号</h3>
            <p class="rule-val">{{ rulesSummary.default_font_size || '--' }} pt</p>
          </div>
          <div class="rule-card">
            <h3>行间距</h3>
            <p class="rule-val">{{ rulesSummary.default_line_spacing || '--' }} 倍</p>
          </div>
          <div class="rule-card wide">
            <h3>标题层级</h3>
            <p class="rule-val">{{ (rulesSummary.heading_levels || []).join(' / ') || '无' }}</p>
          </div>
          <div class="rule-card wide">
            <h3>段落样式</h3>
            <p class="rule-val">{{ [...(rulesSummary.paragraph_styles || []), ...(rulesSummary.caption_styles || [])].join(' / ') || '无' }}</p>
          </div>
        </div>

        <div v-if="isEditingRules && fullRules" class="rules-editor fade-in">
           <!-- ── Segmented Control / Sub Tabs ── -->
           <div class="segmented-control">
             <button class="seg-item" :class="{ active: rulesSubTab === 'general' }" @click="rulesSubTab = 'general'">常规设置</button>
             <button class="seg-item" :class="{ active: rulesSubTab === 'headings' }" @click="rulesSubTab = 'headings'">多级标题</button>
             <button class="seg-item" :class="{ active: rulesSubTab === 'content' }" @click="rulesSubTab = 'content'">正文/备注</button>
             <button class="seg-item" :class="{ active: rulesSubTab === 'advanced' }" @click="rulesSubTab = 'advanced'">高阶插件</button>
           </div>

           <!-- Tab: General -->
           <div v-if="rulesSubTab === 'general'" class="tab-content-fade">
             <div class="editor-section">
               <div class="section-badge">基础设置</div>
               <h3>全局默认格式 (Document)</h3>
               <div class="editor-grid">
                 <div class="form-row"><label>中文字体</label><input class="editor-input" v-model="fullRules.document.default_font_east_asia"/></div>
                 <div class="form-row"><label>英文字体</label><input class="editor-input" v-model="fullRules.document.default_font_ascii"/></div>
                 <div class="form-row"><label>字号(pt)</label><input class="editor-input" type="number" v-model.number="fullRules.document.default_font_size"/></div>
                 <div class="form-row"><label>行距</label><input class="editor-input" type="number" step="0.1" v-model.number="fullRules.document.default_line_spacing"/></div>
               </div>
             </div>

             <div class="editor-section">
               <div class="section-badge">页面</div>
               <h3>页面布局 (Page Setup)</h3>
               <div class="editor-grid">
                 <div class="form-row"><label>上边距(cm)</label><input class="editor-input" type="number" step="0.1" v-model.number="fullRules.page_setup.top_margin_cm"/></div>
                 <div class="form-row"><label>下边距(cm)</label><input class="editor-input" type="number" step="0.1" v-model.number="fullRules.page_setup.bottom_margin_cm"/></div>
                 <div class="form-row"><label>左边距(cm)</label><input class="editor-input" type="number" step="0.1" v-model.number="fullRules.page_setup.left_margin_cm"/></div>
                 <div class="form-row"><label>右边距(cm)</label><input class="editor-input" type="number" step="0.1" v-model.number="fullRules.page_setup.right_margin_cm"/></div>
               </div>
             </div>
           </div>

           <!-- Tab: Headings -->
           <div v-if="rulesSubTab === 'headings'" class="tab-content-fade">
             <div class="editor-section" v-if="fullRules.headings">
               <div class="section-badge">多级标题</div>
               <h3>标题样式定义 (Headings)</h3>
               <div v-for="(hRule, hKey) in fullRules.headings" :key="hKey" class="sub-editor" style="margin-bottom:1.5rem; padding-bottom:1.5rem; border-bottom:1px dashed rgba(255,255,255,0.1)">
                 <h4 style="margin-top:0; color:#cbd5e1; font-size:1rem">{{ hRule.name || hKey }}</h4>
                 <div class="editor-grid">
                   <div class="form-row"><label>中文字体</label><input class="editor-input" v-model="hRule.font_east_asia"/></div>
                   <div class="form-row"><label>英文字体</label><input class="editor-input" v-model="hRule.font_ascii"/></div>
                   <div class="form-row"><label>字号(pt)</label><input class="editor-input" type="number" step="0.5" v-model.number="hRule.font_size"/></div>
                   <div class="form-row"><label>段前间距(pt)</label><input class="editor-input" type="number" step="0.5" v-model.number="hRule.space_before"/></div>
                   <div class="form-row"><label>段后间距(pt)</label><input class="editor-input" type="number" step="0.5" v-model.number="hRule.space_after"/></div>
                   <div class="form-row"><label>对齐方式</label>
                     <select class="editor-input" v-model="hRule.alignment">
                       <option value="left">靠左对齐</option>
                       <option value="center">居中对齐</option>
                       <option value="right">靠右对齐</option>
                       <option value="justify">两端对齐</option>
                     </select>
                   </div>
                   <label class="toggle-label" style="align-self:flex-end; padding-bottom:0.5rem;"><input type="checkbox" v-model="hRule.bold"/> 粗体 (Bold)</label>
                 </div>
               </div>
             </div>
           </div>

           <!-- Tab: Content -->
           <div v-if="rulesSubTab === 'content'" class="tab-content-fade">
             <div class="editor-section">
               <div class="section-badge">正文/题注</div>
               <h3>正文与图表注样式</h3>
               <template v-for="collection in [fullRules.paragraphs, fullRules.captions]">
                 <div v-for="(pRule, pKey) in collection" :key="pKey" class="sub-editor" style="margin-bottom:1.5rem; padding-bottom:1.5rem; border-bottom:1px dashed rgba(255,255,255,0.1)">
                   <h4 style="margin-top:0; color:#cbd5e1; font-size:1rem">{{ pRule.name || pKey }}</h4>
                   <div class="editor-grid">
                     <div class="form-row"><label>中文字体</label><input class="editor-input" v-model="pRule.font_east_asia"/></div>
                     <div class="form-row"><label>英文字体</label><input class="editor-input" v-model="pRule.font_ascii"/></div>
                     <div class="form-row"><label>字号(pt)</label><input class="editor-input" type="number" step="0.5" v-model.number="pRule.font_size"/></div>
                     <div class="form-row"><label>首行缩进(字符)</label><input class="editor-input" type="number" v-model.number="pRule.first_line_indent"/></div>
                     <div class="form-row"><label>对齐方式</label>
                       <select class="editor-input" v-model="pRule.alignment">
                         <option value="left">靠左对齐</option>
                         <option value="center">居中对齐</option>
                         <option value="right">靠右对齐</option>
                         <option value="justify">两端对齐</option>
                       </select>
                     </div>
                     <label class="toggle-label" style="align-self:flex-end; padding-bottom:0.5rem;"><input type="checkbox" v-model="pRule.bold"/> 粗体</label>
                   </div>
                 </div>
               </template>
             </div>
           </div>

           <!-- Tab: Advanced / Plugins -->
           <div v-if="rulesSubTab === 'advanced'" class="tab-content-fade">
             <!-- Pagination Plugin -->
             <div class="editor-section">
               <div class="section-badge">Plugin: Pagination</div>
               <div class="section-header-row">
                 <h3>分页与排版细节</h3>
                 <label class="master-toggle">
                   <input type="checkbox" v-model="fullRules.pagination.enabled" />
                   <span class="toggle-track"></span>
                   <span class="toggle-label-text">开启功能模块</span>
                 </label>
               </div>
               <p class="section-hint">管理论文中的孤行控制、与下段同页、禁止段内分页等高级分页逻辑。</p>
               <div class="editor-grid" v-if="fullRules.pagination.enabled">
                 <label class="toggle-label"><input type="checkbox" v-model="fullRules.pagination.widow_control"/> 开启基础孤行控制 (E009)</label>
                 <div class="form-row">
                   <label>样式穿透 (Keep with next)</label>
                   <input class="editor-input" v-model="fullRules.pagination.keep_with_next_styles_str" placeholder="样式名称，逗号分隔" @blur="fullRules.pagination.keep_with_next_styles = (fullRules.pagination.keep_with_next_styles_str || '').split(',').map(s=>s.trim())"/>
                 </div>
               </div>
             </div>

             <!-- Older Validators -->
             <div class="editor-section">
               <div class="section-badge">分析器总控</div>
               <h3>高阶验证逻辑 (Validators)</h3>
               <div class="editor-flex-row">
                 <label class="toggle-label"><input type="checkbox" v-model="fullRules.validators.check_font"/> 启用字体/字号格式检查 (P0 Core)</label>
                 <label class="toggle-label"><input type="checkbox" v-model="fullRules.validators.check_spacing"/> 启用段落间距/缩进检查 (P1 Core)</label>
                 <label class="toggle-label" style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid rgba(255,255,255,0.05)"><input type="checkbox" v-model="fullRules.validators.check_hierarchy"/> 启用标题层级审查 (拦截伪造/跳段标题)</label>
                 <label class="toggle-label"><input type="checkbox" v-model="fullRules.validators.check_gb7714"/> 启用 GB/T 7714 参考文献格式验证</label>
               </div>
             </div>
           </div>
        </div>

        <div class="action-row" style="margin-top:2rem; flex-wrap:wrap; gap:1.2rem; align-items:center; border-top:1px solid rgba(255,255,255,0.05); padding-top:1.5rem;">
          <div class="library-selector" style="display:flex; flex-direction:column; gap:0.5rem">
            <label style="font-size:0.8rem; color:#64748b; font-weight:600">校级规则库模板</label>
            <div style="display:flex; gap:0.5rem">
              <select class="select" v-model="currentLibrary" style="min-width:180px">
                <option v-for="lib in libraries" :key="lib" :value="lib">{{ lib }}</option>
              </select>
              <button class="btn btn-ghost" @click="switchLibrary">一键应用</button>
            </div>
          </div>

          <div v-if="!isEditingRules" style="display:flex; gap:0.8rem; height:fit-content; margin-top:1.2rem">
            <button class="btn btn-primary" style="background: linear-gradient(135deg, #f59e0b, #d97706);" @click="toggleEditRules">✏️ 可视化编辑</button>
            <button class="btn btn-ghost" @click="downloadRules('yaml')">⬇ 导出</button>
            <label class="btn btn-ghost" style="cursor:pointer">
              ⬆ 导入
              <input type="file" accept=".yaml,.yml,.json" @change="importRules" hidden />
            </label>
            <button class="btn btn-primary" @click="reloadRules">🔄 热重载</button>
          </div>
          <div v-else style="display:flex; gap:0.8rem; height:fit-content; margin-top:1.2rem">
            <button class="btn btn-primary" @click="saveRules">💾 保存并应用</button>
            <button class="btn btn-ghost" @click="toggleEditRules">❌ 取消</button>
          </div>
        </div>
      </div>

      <!-- ── LOGS TAB ────────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'logs'" class="tab-panel">
        <div class="panel-header">
          <h1 class="panel-title">系统运行日志</h1>
          <p class="panel-sub">查看最近系统操作记录、错误信息和关键事件</p>
        </div>

        <div class="action-row" style="margin-bottom: 1.5rem; gap:0.8rem; flex-wrap:wrap">
          <select class="select" v-model="logLevelFilter" @change="loadLogs">
            <option value="">全部级别</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="DEBUG">DEBUG</option>
          </select>
          <button class="btn btn-ghost" @click="loadLogs">🔁 刷新</button>
          <button class="btn btn-ghost" style="color:#f87171; border-color:rgba(248,113,113,0.3)" @click="clearLogs">🗑 清空日志</button>
        </div>

        <div v-if="logsLoading" class="loader-row">
          <div class="spinner"></div><span class="pulse-text">加载日志...</span>
        </div>

        <div v-if="!logsLoading && filteredLogs.length === 0" class="empty-state">
          暂无日志记录
        </div>

        <div class="log-list">
          <div v-for="(log, idx) in filteredLogs" :key="idx" class="log-item">
            <span class="log-ts">{{ log.ts.replace('T', ' ').split('.')[0] }}</span>
            <span class="log-level" :style="{ color: levelColor(log.level) }">{{ log.level }}</span>
            <span class="log-msg">{{ log.msg }}</span>
            <span v-if="log.extra && Object.keys(log.extra).length" class="log-extra">
              {{ JSON.stringify(log.extra) }}
            </span>
          </div>
        </div>
      </div>

      <!-- ── SETTINGS TAB ────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'settings'" class="tab-panel">
        <div class="panel-header">
          <h1 class="panel-title">系统中心</h1>
          <p class="panel-sub">管理校验模块开关、查看系统运行状态及软件更新</p>
        </div>

        <div v-if="isSettingsLoading" class="loader-row">
          <div class="spinner"></div><span class="pulse-text">加载系统配置...</span>
        </div>

        <div v-else-if="systemSettings" class="fade-in">
          <div class="settings-grid">
            <!-- Plugin Management -->
            <div class="settings-card plugin-mgmt">
              <div class="card-header">
                <h3>校验插件流水线 (Pipeline)</h3>
                <span class="badge badge-primary">{{ systemSettings.plugins.filter(p=>p.enabled).length }}/{{ systemSettings.plugins.length }} 已启用</span>
              </div>
              <p class="card-desc">开启或关闭特定的校验规则模块，禁用后相关问题将不再被检测报告。</p>
              
              <div class="plugin-list-new">
                <div v-for="p in systemSettings.plugins" :key="p.id" class="plugin-item-new" @click="togglePlugin(p)">
                  <div class="plugin-info">
                    <span class="name">{{ p.name }}</span>
                    <span class="id">PLUGIN_ID: {{ p.id.toUpperCase() }}</span>
                  </div>
                  <label class="master-toggle" @click.stop>
                    <input type="checkbox" :checked="p.enabled" @change="togglePlugin(p)" />
                    <span class="toggle-track"></span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Version & Maintenance Side -->
            <div class="settings-side-col">
              <div class="settings-card info-card">
                <h3>系统概览</h3>
                <div class="info-list">
                  <div class="info-row"><span class="lbl">软件版本</span><span class="val">{{ systemSettings.version }}</span></div>
                  <div class="info-row"><span class="lbl">编译时间</span><span class="val">{{ systemSettings.build_date }}</span></div>
                  <div class="info-row"><span class="lbl">规则模板</span><span class="val badge-ghost">{{ systemSettings.rules_file }}</span></div>
                  <div class="info-row"><span class="lbl">缓存大小</span><span class="val" style="color:#fb7185">{{ systemSettings.cache_size_mb }} MB</span></div>
                </div>
                <div class="card-footer" style="margin-top: 1.5rem;">
                  <button class="btn btn-ghost" style="width:100%; border-color:#f43f5e22; color:#fb7185" @click="clearSystemCache">🗑 清理空间</button>
                </div>
              </div>

              <div class="settings-card update-card">
                <h3>在线更新</h3>
                <button class="btn btn-primary" :disabled="isCheckingUpdate" @click="checkUpdate" style="width:100%">
                  {{ isCheckingUpdate ? '正在连接 GitHub...' : '检查版本更新' }}
                </button>
                <div v-if="updateInfo" class="update-res fade-in">
                  <div v-if="updateInfo.has_update" class="update-box">
                    <div class="v-tag">New v{{ updateInfo.latest }}</div>
                    <pre class="changes">{{ updateInfo.changelog }}</pre>
                    <a :href="updateInfo.download_url" target="_blank" class="download-link">🔗 点击跳转发布页</a>
                  </div>
                  <div v-else class="v-up-to-date">🎉 当前已是最新版本</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ── Editor ──────────────────────────────────────────────────────────────── */
.rules-editor { display: flex; flex-direction: column; gap: 1.5rem; margin-top: 1rem; }
.editor-section { background: rgba(30,41,59,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; position: relative; }
.editor-section h3 { margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600; color: #e2e8f0; }
.section-badge { position: absolute; top: 1.5rem; right: 1.5rem; background: rgba(99,102,241,0.1); color: #818cf8; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 500; }
.editor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.form-row { display: flex; flex-direction: column; gap: 0.4rem; }
.form-row label { font-size: 0.85rem; color: #94a3b8; }
.editor-input { background: rgba(15,23,42,0.6); border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; padding: 0.6rem 0.8rem; border-radius: 6px; font-family: inherit; transition: all 0.2s; }
.editor-input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
.editor-flex-row { display: flex; flex-direction: column; gap: 0.8rem; }
.toggle-label { display: flex; align-items: center; gap: 0.5rem; color: #cbd5e1; font-size: 0.95rem; cursor: pointer; }
.toggle-label input[type="checkbox"] { width: 1.1rem; height: 1.1rem; accent-color: #6366f1; }

/* ── Segmented Control ── */
.segmented-control {
  display: flex;
  background: rgba(15,23,42,0.6);
  padding: 4px;
  border-radius: 12px;
  margin-bottom: 2rem;
  border: 1px solid rgba(255,255,255,0.05);
  width: fit-content;
}

.seg-item {
  padding: 8px 18px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.seg-item:hover { color: #94a3b8; }
.seg-item.active {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.tab-content-fade {
  animation: tabFade 0.3s ease-out;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@keyframes tabFade {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: none; }
}

/* ── Master Toggle ── */
.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.section-hint {
  font-size: 0.82rem;
  color: #64748b;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.master-toggle {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  cursor: pointer;
}

.master-toggle input { display: none; }

.toggle-track {
  width: 40px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  position: relative;
  transition: background 0.3s;
}

.toggle-track::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.3s;
}

.master-toggle input:checked + .toggle-track { background: #6366f1; }
.master-toggle input:checked + .toggle-track::after { transform: translateX(20px); }
.toggle-label-text { font-size: 0.85rem; color: #818cf8; font-weight: 600; }

/* ── Layout ──────────────────────────────────────────────────────────────── */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: #0d1117;
  color: #e2e8f0;
  position: relative;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: rgba(255,255,255,0.03);
  border-right: 1px solid rgba(255,255,255,0.06);
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0 0.5rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  margin-bottom: 0.8rem;
}

.brand-name {
  font-weight: 700;
  font-size: 1.05rem;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.7rem 1rem;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 0.92rem;
  font-weight: 500;
  text-align: left;
  transition: all 0.18s ease;
}

.nav-item:hover { background: rgba(255,255,255,0.05); color: #94a3b8; }
.nav-item.active { background: linear-gradient(135deg, rgba(96,165,250,0.15), rgba(167,139,250,0.12)); color: #a5c8ff; border: 1px solid rgba(96,165,250,0.2); }

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 2.5rem 3rem;
}

/* ── Panel Header ────────────────────────────────────────────────────────── */
.panel-header { margin-bottom: 2.5rem; }

.panel-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  background: linear-gradient(135deg, #e2e8f0, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.panel-sub { margin: 0; color: #64748b; font-size: 0.95rem; }

/* ── Dropzone ────────────────────────────────────────────────────────────── */
.dropzone {
  border: 2px dashed rgba(148,163,184,0.25);
  border-radius: 20px;
  padding: 3.5rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  background: rgba(15,23,42,0.3);
}

.dropzone:hover { border-color: rgba(96,165,250,0.45); background: rgba(15,23,42,0.55); }
.dropzone.active { border-color: #60a5fa; background: rgba(96,165,250,0.08); transform: scale(1.015); }

.upload-icon { color: #818cf8; transition: transform 0.3s ease; }
.dropzone:hover .upload-icon { transform: translateY(-4px); }

.upload-btn {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  padding: 10px 28px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  color: #fff;
  font-size: 0.9rem;
  box-shadow: 0 4px 15px rgba(99,102,241,0.35);
  transition: all 0.2s;
}

.upload-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99,102,241,0.55); }

.drop-hint { color: #475569; font-size: 0.85rem; }
.file-badge { background: rgba(96,165,250,0.12); border: 1px solid rgba(96,165,250,0.25); padding: 6px 16px; border-radius: 8px; font-size: 0.85rem; color: #93c5fd; }

/* ── Loader ──────────────────────────────────────────────────────────────── */
.loader-row { display: flex; align-items: center; gap: 1rem; margin-top: 2.5rem; }
.spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-left-color: #60a5fa; border-radius: 50%; animation: spin 0.9s linear infinite; flex-shrink:0; }
@keyframes spin { to { transform: rotate(360deg); } }
.pulse-text { color: #64748b; animation: pulse 1.8s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:0.6; } 50% { opacity:1; } }

/* ── Stats Row ───────────────────────────────────────────────────────────── */
.stats-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat-card {
  flex: 1;
  min-width: 120px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.stat-num { font-size: 2rem; font-weight: 700; }
.stat-label { font-size: 0.78rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Action Row ──────────────────────────────────────────────────────────── */
.action-row { display: flex; gap: 0.8rem; margin-bottom: 1.5rem; align-items: center; }

.btn {
  padding: 9px 20px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.18s ease;
}

.btn-ghost { background: transparent; border-color: rgba(255,255,255,0.12); color: #94a3b8; }
.btn-ghost:hover { background: rgba(255,255,255,0.06); color: #e2e8f0; }
.btn-primary { background: linear-gradient(135deg, #4f46e5, #7c3aed); color: #fff; box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(99,102,241,0.45); }
.btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Issue Cards ────────────────────────────────────────────────────────────*/
.issues-list { display: flex; flex-direction: column; gap: 1rem; }

.issue-card {
  background: rgba(30,41,59,0.6);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 1.1rem 1.3rem;
  border-left-width: 4px;
  transition: transform 0.18s ease;
}

.issue-card:hover { transform: translateX(4px); }
.is-error { border-left-color: #ef4444; }
.is-warn  { border-left-color: #f59e0b; }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
.badge { padding: 3px 10px; border-radius: 100px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; }
.badge-error { background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.badge-warn  { background: rgba(245,158,11,0.18); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }

.para-id { color: #475569; font-size: 0.8rem; font-family: monospace; }
.context { color: #94a3b8; font-style: italic; margin: 0 0 0.4rem; font-size: 0.88rem; }
.msg { color: #fda4af; margin: 0; font-size: 0.9rem; font-weight: 500; }

/* ── Success ────────────────────────────────────────────────────────────── */
.success-box {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 3.5rem;
  background: rgba(74,222,128,0.05); border: 1px dashed rgba(74,222,128,0.3);
  border-radius: 16px; color: #4ade80; gap: 1rem;
}

/* ── Rules Tab ────────────────────────────────────────────────────────────*/
.rules-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.rule-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1.2rem 1.4rem;
}
.rule-card.wide { grid-column: span 2; }
.rule-card h3 { margin: 0 0 0.5rem; font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
.rule-val { margin: 0; font-size: 1.1rem; font-weight: 600; color: #a5c8ff; }

.select {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  padding: 8px 12px;
  color: #94a3b8;
  font-size: 0.88rem;
  cursor: pointer;
  outline: none;
}

/* ── Log Tab ─────────────────────────────────────────────────────────────── */
.log-list { display: flex; flex-direction: column; gap: 0.3rem; font-family: monospace; font-size: 0.82rem; }

.log-item {
  display: flex;
  align-items: baseline;
  gap: 0.7rem;
  padding: 0.5rem 0.8rem;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  transition: background 0.15s;
  flex-wrap: wrap;
}

.log-item:hover { background: rgba(255,255,255,0.04); }
.log-ts { color: #475569; flex-shrink: 0; }
.log-level { font-weight: 700; min-width: 64px; flex-shrink: 0; }
.log-msg { color: #cbd5e1; flex: 1; word-break: break-word; }
.log-extra { color: #64748b; font-size: 0.76rem; word-break: break-all; width: 100%; }

.empty-state { text-align: center; padding: 4rem; color: #475569; }

/* ── Toast ────────────────────────────────────────────────────────────────── */
.toast {
  position: fixed; bottom: 2rem; right: 2rem; z-index: 999;
  background: rgba(30,41,59,0.95);
  border: 1px solid rgba(96,165,250,0.3);
  color: #a5c8ff;
  padding: 0.8rem 1.4rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  backdrop-filter: blur(12px);
}

.toast-enter-active, .toast-leave-active { transition: all 0.28s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(12px); }

/* ── Animations ────────────────────────────────────────────────────────────── */
/* ── Progress Box (P5) ───────────────────────────────────────────────────── */
.progress-box { flex: 1; display: flex; flex-direction: column; gap: 0.6rem; }
.progress-info { display: flex; justify-content: space-between; align-items: center; }
.progress-bar-bg { height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, #60a5fa, #a78bfa); transition: width 0.3s ease; }

.fade-in { animation: fadeIn 0.4s ease forwards; }
@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }

/* ── Settings Panel Styles ── */
/* ── Settings Tab Styles ── */
.settings-grid { display: grid; grid-template-columns: 1fr 340px; gap: 2rem; align-items: start; }
.settings-card { background: rgba(30,41,59,0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 18px; padding: 1.8rem; }
.settings-card h3 { margin: 0 0 1.2rem 0; font-size: 1.15rem; color: #f1f5f9; display: flex; align-items: center; justify-content: space-between; }
.card-desc { font-size: 0.88rem; color: #64748b; margin-bottom: 1.8rem; line-height: 1.6; }

.plugin-mgmt { min-height: 500px; }
.plugin-list-new { display: flex; flex-direction: column; gap: 0.8rem; }
.plugin-item-new {
  background: rgba(15,23,42,0.4); border: 1px solid rgba(255,255,255,0.04);
  padding: 1.2rem 1.5rem; border-radius: 14px;
  display: flex; justify-content: space-between; align-items: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}
.plugin-item-new:hover { background: rgba(30,58,138,0.15); border-color: rgba(59,130,246,0.3); transform: translateX(1px); }
.plugin-info { display: flex; flex-direction: column; gap: 0.2rem; }
.plugin-info .name { font-size: 1rem; color: #e2e8f0; font-weight: 600; }
.plugin-info .id { font-size: 0.72rem; color: #475569; font-family: monospace; letter-spacing: 0.05em; }

.settings-side-col { display: flex; flex-direction: column; gap: 2rem; }
.info-list { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }
.info-row { display: flex; justify-content: space-between; font-size: 0.92rem; }
.info-row .lbl { color: #64748b; }
.info-row .val { color: #cbd5e1; font-weight: 500; font-family: monospace; }
.badge-ghost { background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }

.update-res { margin-top: 1.5rem; }
.update-box { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); padding: 1.2rem; border-radius: 12px; }
.v-tag { display: inline-block; background: #f59e0b; color: #000; font-weight: 800; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; margin-bottom: 0.8rem; }
.changes { font-family: inherit; font-size: 0.82rem; color: #d97706; margin: 0 0 1rem 0; white-space: pre-wrap; line-height: 1.5; }
.download-link { font-size: 0.85rem; color: #f59e0b; text-decoration: none; font-weight: 600; border-bottom: 1px dashed; }
.v-up-to-date { text-align: center; color: #10b981; font-weight: 600; font-size: 0.9rem; }

.fade-in-right { animation: fadeInRight 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
@keyframes fadeInRight { from { opacity: 0; transform: translateX(50px); } to { opacity: 1; transform: none; } }
</style>
