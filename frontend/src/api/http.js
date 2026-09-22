import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器
http.interceptors.request.use((config) => {
  const tokenKey = config.admin ? 'admin_access_token' : 'access_token'
  const token = localStorage.getItem(tokenKey)

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'

    if (error.response?.status === 401) {
      if (error.config?.admin) {
        localStorage.removeItem('admin_access_token')
        localStorage.removeItem('admin_user')
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
      }
    }

    if (!error.config?.silent) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  },
)

export default http
