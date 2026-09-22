<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  CirclePlus,
  Delete,
  Promotion,
  Refresh,
  Tools,
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'

import {
  deleteChatSession,
  fetchChatSessionDetail,
  fetchChatSessions,
  streamAiChatMessage,
} from '../api/aiChat'
import { useAuthStore } from '../stores/auth'

const SESSION_STORAGE_KEY = 'hotel_ai_chat_session'

const authStore = useAuthStore()

// 使用 markdown-it 渲染模型输出的列表与加粗内容。
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)
const sessionId = ref(localStorage.getItem(SESSION_STORAGE_KEY) || '')
const chatBodyRef = ref(null)

const quickPrompts = [
  '帮我推荐一间两人入住、含早餐、有窗的房间',
  '我之前的订单和收藏偏好是什么样的？',
  '有没有 200 元以内的高性价比房型？',
  '帮我预订一间 5 月 1 日到 5 月 3 日的大床房',
]

const welcomeTips = [
  { title: '房型推荐', desc: '告诉我人数、预算与偏好，我会结合你的收藏优先推荐。' },
  { title: '偏好分析', desc: '我会读取历史订单与收藏，解释为什么这些房型适合你。' },
  { title: '自动下单', desc: '确认房型与日期后，我会自动使用你的资料完成预订登记。' },
]

// 智能体当前是否处于思考状态。
const thinking = computed(() => loading.value)

function createLocalId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function renderMarkdown(content) {
  return md.render(content || '')
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatBodyRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function findReplyMessage(id) {
  return messages.value.find((item) => item.id === id)
}

// 加载历史会话列表。
async function loadSessions() {
  sessionsLoading.value = true
  try {
    const response = await fetchChatSessions()
    if (response.data?.code === 200) {
      sessions.value = response.data.data || []
    }
  } finally {
    sessionsLoading.value = false
  }
}

// 打开某个历史会话。
async function openSession(target) {
  if (loading.value) {
    ElMessage.warning('智能体正在回复中，请稍候再切换会话')
    return
  }

  const response = await fetchChatSessionDetail(target.session_id)
  if (response.data?.code === 200) {
    sessionId.value = target.session_id
    localStorage.setItem(SESSION_STORAGE_KEY, target.session_id)
    messages.value = (response.data.data.messages || []).map((item) => ({
      id: item.id,
      role: item.role,
      kind: item.kind,
      content: item.content,
      process: item.process,
      created_at: item.created_at,
    }))
    scrollToBottom()
  }
}

// 删除历史会话。
async function handleDeleteSession(target) {
  try {
    await ElMessageBox.confirm(`确认删除会话「${target.title}」吗？`, '删除会话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  const response = await deleteChatSession(target.session_id)
  if (response.data?.code === 200) {
    ElMessage.success('会话已删除')
    if (sessionId.value === target.session_id) {
      startNewChat()
    }
    await loadSessions()
  }
}

// 开启一段新的对话。
function startNewChat() {
  messages.value = []
  sessionId.value = ''
  localStorage.removeItem(SESSION_STORAGE_KEY)
}

// 把过程消息同步到聊天流中。
function syncProcessMessagesToChat(processMessages, turnId, shownKeys, replyMessageId) {
  processMessages.forEach((item, index) => {
    // 用户消息与最终回复已有独立气泡，无需重复展示为过程卡片。
    if (item.type === 'human') return
    if (item.type === 'ai' && !item.has_tool_calls) return

    const key = `${item.type}-${item.title}-${index}`
    if (shownKeys.has(key)) return
    shownKeys.add(key)

    const processIndex = messages.value.findIndex((m) => m.id === replyMessageId)
    const card = {
      id: `${turnId}-process-${index}`,
      role: 'assistant',
      kind: 'process',
      content: item.title || '执行过程',
      process: item,
    }

    if (processIndex === -1) {
      messages.value.push(card)
    } else {
      messages.value.splice(processIndex, 0, card)
    }
  })
}

// 发送消息并处理流式事件。
async function handleSend(messageText = '') {
  const content = (messageText || inputMessage.value).trim()
  if (!content || loading.value) return

  const turnId = createLocalId('turn')
  const replyMessageId = `${turnId}-reply`
  const shownProcessKeys = new Set()
  messages.value.push({ id: `${turnId}-user`, role: 'user', kind: 'text', content })
  messages.value.push({
    id: replyMessageId,
    role: 'assistant',
    kind: 'reply',
    content: '智能体正在分析你的需求...',
    streaming: true,
  })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  try {
    await streamAiChatMessage(
      { message: content, session_id: sessionId.value },
      {
        onStart(data) {
          if (data.session_id && !sessionId.value) {
            sessionId.value = data.session_id
            localStorage.setItem(SESSION_STORAGE_KEY, data.session_id)
          }
        },
        onToken(data) {
          if (data.session_id) {
            sessionId.value = data.session_id
            localStorage.setItem(SESSION_STORAGE_KEY, data.session_id)
          }
          const replyMessage = findReplyMessage(replyMessageId)
          if (replyMessage) {
            replyMessage.content = data.reply || `${replyMessage.content || ''}${data.token || ''}`
          }
          scrollToBottom()
        },
        onMessage(data) {
          if (data.session_id) {
            sessionId.value = data.session_id
          }
          syncProcessMessagesToChat(
            data.process_messages || [],
            turnId,
            shownProcessKeys,
            replyMessageId,
          )
          scrollToBottom()
        },
        onDone(data) {
          const replyMessage = findReplyMessage(replyMessageId)
          if (replyMessage) {
            replyMessage.content = data.reply || replyMessage.content
            replyMessage.streaming = false
          }
          loadSessions()
          scrollToBottom()
        },
        onError(data) {
          const replyMessage = findReplyMessage(replyMessageId)
          if (replyMessage) {
            replyMessage.content = data.reply || '智能体执行失败，请稍后重试。'
            replyMessage.streaming = false
          }
        },
      },
    )
  } catch (err) {
    const replyMessage = findReplyMessage(replyMessageId)
    if (replyMessage) {
      replyMessage.content = err.message || 'AI 智能体请求失败，请确认后端服务与大模型密钥配置。'
      replyMessage.streaming = false
    }
    ElMessage.error(err.message || 'AI 智能体请求失败')
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<template>
  <main class="ai-chat-page">
    <div class="ai-chat-body">
      <!-- 左侧会话列表 -->
      <aside class="session-panel">
        <div class="session-head">
          <h2>
            <el-icon><ChatDotRound /></el-icon>
            智能预订助手
          </h2>
          <p>LangGraph ReAct 智能体 · 自动查房下单</p>
        </div>

        <el-button class="new-chat-btn" :icon="CirclePlus" @click="startNewChat">
          开启新对话
        </el-button>

        <div v-loading="sessionsLoading" class="session-list">
          <div v-if="sessions.length === 0" class="session-empty">暂无历史会话</div>
          <div
            v-for="item in sessions"
            :key="item.id"
            class="session-item"
            :class="{ active: item.session_id === sessionId }"
            @click="openSession(item)"
          >
            <div class="session-info">
              <span class="session-title">{{ item.title }}</span>
              <span class="session-meta">{{ item.message_count }} 条消息</span>
            </div>
            <el-icon class="session-delete" @click.stop="handleDeleteSession(item)">
              <Delete />
            </el-icon>
          </div>
        </div>
      </aside>

      <!-- 右侧对话区 -->
      <section class="chat-panel">
        <header class="chat-head">
          <div>
            <h3>AI 预订助手</h3>
            <span class="chat-sub">
              {{ authStore.user?.username }} · 会话 {{ sessionId ? sessionId.substring(0, 8) : '新会话' }}
            </span>
          </div>
          <el-button plain size="small" :icon="Refresh" @click="loadSessions">刷新会话</el-button>
        </header>

        <div ref="chatBodyRef" class="chat-body">
          <!-- 欢迎区 -->
          <div v-if="messages.length === 0" class="chat-welcome">
            <div class="welcome-icon">
              <el-icon><Promotion /></el-icon>
            </div>
            <h2>您好，我是友家快捷酒店的 AI 订房助手</h2>
            <p>我可以帮您查询房型、分析偏好，并在您确认后直接完成预订登记。</p>

            <div class="welcome-tips">
              <div v-for="tip in welcomeTips" :key="tip.title" class="tip-card">
                <strong>{{ tip.title }}</strong>
                <span>{{ tip.desc }}</span>
              </div>
            </div>

            <div class="quick-prompts">
              <button
                v-for="prompt in quickPrompts"
                :key="prompt"
                type="button"
                class="prompt-chip"
                @click="handleSend(prompt)"
              >
                {{ prompt }}
              </button>
            </div>
          </div>

          <!-- 消息流 -->
          <template v-else>
            <div
              v-for="item in messages"
              :key="item.id"
              class="message-row"
              :class="item.role === 'user' ? 'from-user' : 'from-ai'"
            >
              <!-- 过程卡片 -->
              <div v-if="item.kind === 'process'" class="process-card">
                <div class="process-head">
                  <el-icon><Tools /></el-icon>
                  <span>{{ item.content }}</span>
                </div>
                <el-collapse class="process-collapse">
                  <el-collapse-item title="查看执行细节">
                    <div class="process-detail">
                      <div v-if="item.process?.tool_calls?.length" class="detail-block">
                        <span class="detail-label">工具调用参数</span>
                        <pre v-for="call in item.process.tool_calls" :key="call.id || call.name">{{
                          `${call.name}(${JSON.stringify(call.args || {}, null, 2)})`
                        }}</pre>
                      </div>
                      <div v-else class="detail-block">
                        <span class="detail-label">返回结果</span>
                        <pre>{{ item.process?.content }}</pre>
                      </div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 文本气泡 -->
              <div v-else class="bubble" :class="{ streaming: item.streaming }">
                <div
                  v-if="item.role === 'assistant'"
                  class="markdown-body"
                  v-html="renderMarkdown(item.content)"
                ></div>
                <div v-else class="plain-text">{{ item.content }}</div>
              </div>
            </div>
          </template>

          <div v-if="thinking" class="thinking-row">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="thinking-text">智能体正在推理与调用工具…</span>
          </div>
        </div>

        <footer class="chat-input-bar">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            resize="none"
            maxlength="500"
            placeholder="请输入您的住宿需求，例如：帮我推荐一间两人入住、含早餐的房间"
            @keydown.enter.exact.prevent="handleSend()"
          />
          <el-button
            class="send-btn"
            :icon="Promotion"
            :loading="loading"
            @click="handleSend()"
          >
            发送
          </el-button>
        </footer>
      </section>
    </div>
  </main>
</template>

<style scoped>
.ai-chat-page {
  min-height: calc(100vh - 72px);
  background-color: #f4f7fb;
  padding: 26px 24px 40px;
}

.ai-chat-body {
  max-width: 1240px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 22px;
  height: calc(100vh - 72px - 66px);
  min-height: 620px;
}

/* 左侧会话面板 */
.session-panel {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.03);
  overflow: hidden;
}

.session-head h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 6px;
}

.session-head h2 .el-icon {
  color: #4f8ef7;
}

.session-head p {
  font-size: 11px;
  color: #9fadc0;
  margin: 0;
  font-weight: 600;
}

.new-chat-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  border-radius: 10px;
  height: 40px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
}

.session-empty {
  font-size: 12px;
  color: #c3cddb;
  text-align: center;
  padding: 20px 0;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.22s ease;
}

.session-item:hover {
  background: #f5f6f2;
}

.session-item.active {
  background: rgba(22, 50, 79, 0.06);
  border-color: rgba(22, 50, 79, 0.18);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 12.5px;
  font-weight: 700;
  color: #1a2b40;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: block;
  font-size: 10.5px;
  color: #9fadc0;
  margin-top: 3px;
}

.session-delete {
  color: #cbd5e0;
  font-size: 14px;
  transition: color 0.2s ease;
}

.session-delete:hover {
  color: #e74c3c;
}

/* 右侧对话区 */
.chat-panel {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.03);
}

.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(22, 50, 79, 0.08);
  background: #fbfdff;
}

.chat-head h3 {
  font-size: 16px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 4px;
}

.chat-sub {
  font-size: 11px;
  color: #9fadc0;
  font-weight: 600;
}

/* 消息区 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 26px 26px 10px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
}

.chat-welcome {
  text-align: center;
  padding: 20px 10px;
  margin: auto 0;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(22, 50, 79, 0.06);
  color: #16324f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 18px;
}

.chat-welcome h2 {
  font-size: 21px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 10px;
  font-family: 'Georgia', serif;
}

.chat-welcome p {
  font-size: 13px;
  color: #8494ab;
  margin: 0 0 28px;
}

.welcome-tips {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  max-width: 760px;
  margin: 0 auto 26px;
}

.tip-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 12px;
  padding: 18px 16px;
  text-align: left;
}

.tip-card strong {
  display: block;
  font-size: 13px;
  font-weight: 800;
  color: #16324f;
  margin-bottom: 8px;
}

.tip-card span {
  font-size: 12px;
  line-height: 1.6;
  color: #8494ab;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.prompt-chip {
  background: #edf2f8;
  border: 1px solid transparent;
  border-radius: 24px;
  padding: 9px 18px;
  font-size: 12.5px;
  color: #46566b;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.22s ease;
}

.prompt-chip:hover {
  background: #16324f;
  color: #ffffff;
}

/* 消息行 */
.message-row {
  display: flex;
  flex-direction: column;
}

.message-row.from-user {
  align-items: flex-end;
}

.message-row.from-ai {
  align-items: flex-start;
}

.bubble {
  max-width: 78%;
  border-radius: 14px;
  padding: 13px 17px;
  font-size: 13.5px;
  line-height: 1.75;
  word-break: break-word;
}

.from-user .bubble {
  background: #16324f;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.from-ai .bubble {
  background: #f6f7f4;
  color: #2f3a34;
  border: 1px solid rgba(22, 50, 79, 0.06);
  border-bottom-left-radius: 4px;
  max-width: 88%;
}

.plain-text {
  white-space: pre-wrap;
}

/* Markdown 渲染样式 */
.markdown-body :deep(p) {
  margin: 0 0 10px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0 10px;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.markdown-body :deep(strong) {
  color: #16324f;
  font-weight: 800;
}

.markdown-body :deep(code) {
  background: rgba(22, 50, 79, 0.07);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12.5px;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12.5px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(22, 50, 79, 0.12);
  padding: 6px 10px;
}

/* 过程卡片 */
.process-card {
  max-width: 88%;
  background: #fdfaf5;
  border: 1px dashed rgba(79, 142, 247, 0.6);
  border-radius: 12px;
  padding: 12px 16px;
}

.process-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  font-weight: 800;
  color: #2f6fd8;
}

.process-collapse {
  margin-top: 6px;
  --el-collapse-header-height: 32px;
}

.process-collapse :deep(.el-collapse-item__header) {
  font-size: 12px;
  font-weight: 700;
  color: #b08a4f;
  background: transparent;
  border-bottom: none;
}

.process-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border-bottom: none;
}

.process-collapse :deep(.el-collapse-item__content) {
  padding-bottom: 4px;
}

.process-detail {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 11px;
  font-weight: 800;
  color: #9fadc0;
  letter-spacing: 0.4px;
}

.process-detail pre {
  margin: 4px 0 0;
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 11.5px;
  line-height: 1.6;
  color: #46566b;
  max-height: 220px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Consolas', 'Menlo', monospace;
}

/* 思考动画 */
.thinking-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 4px;
}

.thinking-row .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4f8ef7;
  animation: bounce 1.2s infinite ease-in-out;
}

.thinking-row .dot:nth-child(2) {
  animation-delay: 0.16s;
}

.thinking-row .dot:nth-child(3) {
  animation-delay: 0.32s;
}

.thinking-text {
  font-size: 12px;
  color: #9fadc0;
  margin-left: 6px;
  font-weight: 600;
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40% { transform: translateY(-5px); opacity: 1; }
}

/* 输入区 */
.chat-input-bar {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 16px 22px 20px;
  border-top: 1px solid rgba(22, 50, 79, 0.08);
  background: #fbfdff;
}

.chat-input-bar :deep(.el-textarea__inner) {
  border-radius: 12px;
  font-size: 13.5px;
  line-height: 1.6;
  padding: 12px 14px;
  box-shadow: none;
  border: 1px solid rgba(22, 50, 79, 0.14);
  resize: none;
}

.chat-input-bar :deep(.el-textarea__inner:focus) {
  border-color: #4f8ef7;
}

.send-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  height: 44px;
  border-radius: 12px;
  padding: 0 26px;
}

.send-btn:hover {
  background: #1a2b40 !important;
}

@media (max-width: 992px) {
  .ai-chat-body {
    grid-template-columns: 1fr;
    height: auto;
  }

  .session-panel {
    max-height: 260px;
  }

  .welcome-tips {
    grid-template-columns: 1fr;
  }

  .chat-body {
    min-height: 420px;
  }
}
</style>
