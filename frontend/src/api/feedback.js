import http from './http'

// 获取当前用户提交过的留言反馈
export function fetchFeedbacks() {
  return http.get('/feedback/')
}

// 提交新的留言反馈
export function createFeedback(data) {
  return http.post('/feedback/', data)
}
