import http from './http'

// 用户注册
export function registerUser(data) {
  return http.post('/accounts/register/', data)
}

// 用户登录
export function loginAccount(data) {
  return http.post('/accounts/login/', data)
}

// 获取用户资料
export function fetchProfile() {
  return http.get('/accounts/profile/')
}

// 更新用户资料（支持 multipart 头像上传）
export function updateProfile(data) {
  return http.patch('/accounts/profile/', data)
}

// 修改登录密码
export function changePassword(data) {
  return http.post('/accounts/change-password/', data)
}

// 退出登录
export function logoutAccount() {
  return http.post('/accounts/logout/')
}
