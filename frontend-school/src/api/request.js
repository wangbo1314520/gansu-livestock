import axios from 'axios'
import { ElMessage } from 'element-plus'

// axios 统一封装： baseURL / token 注入 / 统一错误提示
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端统一格式 {code, msg, data}
    if (res.code === 200) {
      return res.data
    }
    ElMessage.error(res.msg || '请求失败')
    return Promise.reject(new Error(res.msg))
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      ElMessage.error('登录已过期，请重新登录')
      window.location.href = '/login'
    } else {
      const msg = (error.response && error.response.data && error.response.data.msg) || error.message
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default request
