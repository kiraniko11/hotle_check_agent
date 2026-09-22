import http from './http'

// 管理员登录（独立令牌通道）
export function adminLogin(data) {
  return http.post('/admin-panel/login/', data, { admin: true })
}

// 获取当前登录管理员资料
export function fetchAdminProfile() {
  return http.get('/admin-panel/profile/', { admin: true })
}

// 获取后台全局统计指标
export function fetchAdminStats() {
  return http.get('/admin-panel/stats/', { admin: true })
}

// 通用资源接口：资源名作为参数，七个资源共用同一套方法。
export function fetchAdminResource(resource, params = {}) {
  return http.get(`/admin-panel/${resource}/`, { params, admin: true })
}

export function createAdminResource(resource, payload) {
  return http.post(`/admin-panel/${resource}/`, payload, { admin: true })
}

export function updateAdminResource(resource, id, payload) {
  return http.patch(`/admin-panel/${resource}/${id}/`, payload, { admin: true })
}

export function deleteAdminResource(resource, id) {
  return http.delete(`/admin-panel/${resource}/${id}/`, { admin: true })
}
