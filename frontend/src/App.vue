<script setup>
import { ref, computed } from 'vue'

const API = 'http://127.0.0.1:8000'

// ── State ────────────────────────────────────────────────────────────────────
const activeTab = ref('check')   // 'check' | 'rules' | 'logs'
const isDragging = ref(false)
const loading = ref(false)
const validationDone = ref(false)
const fileName = ref('')
const uploadedFile = ref(null)
const issues = ref([])
const checkedAt = ref('')

const rulesLoading = ref(false)
const rulesSummary = ref(null)
const logsLoading = ref(false)
const logs = ref([])
const logLevelFilter = ref('')

const exporting = ref(false)

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
  issues.value = []
  validationDone.value = false

  const fd = new FormData()
  fd.append('file', file)

  try {
    const res = await fetch(`${API}/api/check`, { method: 'POST', body: fd })
    const data = await res.json()
    issues.value = data.issues || []
    checkedAt.value = data.checked_at
    validationDone.value = true
  } catch (err) {
    alert('校验服务不可达，请检查后端是否运行')
    console.error(err)
  } finally {
    loading.value = false
  }
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
    const res = await fetch(`${API}/api/export/annotated`, { method: 'POST', body: fd })
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

// ── Rules Tab ─────────────────────────────────────────────────────────────────
const loadRulesSummary = async () => {
  rulesLoading.value = true
  try {
    const res = await fetch(`${API}/api/rules/summary`)
    rulesSummary.value = await res.json()
  } finally {
    rulesLoading.value = false
  }
}

const downloadRules = async (fmt) => {
  const res = await fetch(`${API}/api/rules/export/${fmt}`)
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
    const res = await fetch(`${API}/api/rules/import`, { method: 'POST', body: fd })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '导入失败')
    showToast(data.message || '规则导入成功')
    await loadRulesSummary()
  } catch (err) {
    alert(`规则导入失败：${err.message}`)
  }
}

const reloadRules = async () => {
  const res = await fetch(`${API}/api/rules/reload`, { method: 'POST' })
  const data = await res.json()
  showToast(data.message)
  await loadRulesSummary()
}

// ── Logs Tab ──────────────────────────────────────────────────────────────────
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const url = logLevelFilter.value
      ? `${API}/api/logs?limit=200&level=${logLevelFilter.value}`
      : `${API}/api/logs?limit=200`
    const res = await fetch(url)
    const data = await res.json()
    logs.value = (data.logs || []).reverse()
  } finally {
    logsLoading.value = false
  }
}

const clearLogs = async () => {
  if (!confirm('确认清空所有日志记录？')) return
  await fetch(`${API}/api/logs`, { method: 'DELETE' })
  logs.value = []
  showToast('日志已清空')
}

// ── Tab switch side-effects ───────────────────────────────────────────────────
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'rules' && !rulesSummary.value) loadRulesSummary()
  if (tab === 'logs') loadLogs()
}

// ── Toast Notification ────────────────────────────────────────────────────────
const toast = ref(null)
const showToast = (msg) => {
  toast.value = msg
  setTimeout(() => { toast.value = null }, 2800)
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
          <span class="pulse-text">深度解析引擎运行中，逐段式结构比对中...</span>
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
            <button class="btn btn-ghost" @click="copyReport">
              📋 复制报告文本
            </button>
            <button class="btn btn-primary" :disabled="exporting || !issues.length" @click="exportAnnotated">
              <span v-if="exporting">导出中...</span>
              <span v-else>📥 导出批注 Docx</span>
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

        <div v-if="rulesSummary" class="rules-grid fade-in">
          <div class="rule-card">
            <h3>中文正文字体</h3>
            <p class="rule-val">{{ rulesSummary.default_font_east_asia }}</p>
          </div>
          <div class="rule-card">
            <h3>英文字体</h3>
            <p class="rule-val">{{ rulesSummary.default_font_ascii }}</p>
          </div>
          <div class="rule-card">
            <h3>缺省字号</h3>
            <p class="rule-val">{{ rulesSummary.default_font_size }} pt</p>
          </div>
          <div class="rule-card">
            <h3>行间距</h3>
            <p class="rule-val">{{ rulesSummary.default_line_spacing }} 倍</p>
          </div>
          <div class="rule-card wide">
            <h3>标题层级</h3>
            <p class="rule-val">{{ rulesSummary.heading_levels.join(' / ') }}</p>
          </div>
          <div class="rule-card wide">
            <h3>段落样式</h3>
            <p class="rule-val">{{ [...rulesSummary.paragraph_styles, ...rulesSummary.caption_styles].join(' / ') }}</p>
          </div>
        </div>

        <div class="action-row" style="margin-top:2rem; flex-wrap:wrap; gap:0.8rem">
          <button class="btn btn-ghost" @click="downloadRules('yaml')">⬇ 导出 YAML</button>
          <button class="btn btn-ghost" @click="downloadRules('json')">⬇ 导出 JSON</button>
          <label class="btn btn-ghost" style="cursor:pointer">
            ⬆ 导入规则文件
            <input type="file" accept=".yaml,.yml,.json" @change="importRules" hidden />
          </label>
          <button class="btn btn-primary" @click="reloadRules">🔄 热重载规则</button>
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
    </main>
  </div>
</template>

<style scoped>
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
.fade-in { animation: fadeIn 0.4s ease forwards; }
@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
</style>
