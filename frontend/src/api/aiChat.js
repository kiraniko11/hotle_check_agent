import http from './http'

// 获取历史 AI 对话会话列表
export function fetchChatSessions() {
  return http.get('/ai-chat/sessions/')
}

// 获取指定会话的完整消息记录
export function fetchChatSessionDetail(sessionId) {
  return http.get(`/ai-chat/sessions/${sessionId}/`)
}

// 删除指定会话
export function deleteChatSession(sessionId) {
  return http.delete(`/ai-chat/sessions/${sessionId}/`)
}

// 以流式方式发送消息。
// 浏览器原生 EventSource 不支持 POST 与自定义请求头，因此使用 fetch 手动解析 SSE。
export async function streamAiChatMessage(data, handlers = {}) {
  const token = localStorage.getItem('access_token')

  const response = await fetch('/api/ai-chat/chat/stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  })

  if (!response.ok || !response.body) {
    let message = 'AI 智能体流式请求失败'
    try {
      const errorPayload = await response.json()
      message = errorPayload.msg || errorPayload.detail || message
    } catch {
      // 响应体不是 JSON 时沿用默认提示。
    }
    throw new Error(message)
  }

  // 后端若因异常返回普通 JSON 而非 SSE，这里直接抛出，避免页面静默无响应。
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    let message = 'AI 智能体流式请求失败'
    try {
      const payload = await response.json()
      message = payload.msg || payload.detail || message
    } catch {
      // 响应体解析失败时沿用默认提示。
    }
    throw new Error(message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  function dispatchEventBlock(block) {
    const eventLine = block.split('\n').find((line) => line.startsWith('event:'))
    const dataLines = block
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.replace(/^data:\s?/, ''))
    if (!eventLine || dataLines.length === 0) return

    const eventName = eventLine.replace(/^event:\s?/, '').trim()
    let payload
    try {
      payload = JSON.parse(dataLines.join('\n'))
    } catch {
      return
    }

    if (eventName === 'start') handlers.onStart?.(payload)
    else if (eventName === 'token') handlers.onToken?.(payload)
    else if (eventName === 'message') handlers.onMessage?.(payload)
    else if (eventName === 'done') handlers.onDone?.(payload)
    else if (eventName === 'error') handlers.onError?.(payload)
  }

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // 只处理以空行分隔的完整事件块，剩余半截事件留到下一次读取后拼接。
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    blocks.forEach(dispatchEventBlock)
  }

  if (buffer.trim()) {
    dispatchEventBlock(buffer)
  }
}
