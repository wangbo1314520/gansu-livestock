import axios from 'axios'
import { showToast } from 'vant'

// axios 统一封装：移动端用 toast 提示错误
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
    if (res.code === 200) {
      return res.data
    }
    showToast(res.msg || '请求失败')
    return Promise.reject(new Error(res.msg))
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      showToast('登录已过期')
      window.location.href = '/login'
    } else {
      const msg = (error.response && error.response.data && error.response.data.msg) || error.message
      showToast(msg)
    }
    return Promise.reject(error)
  },
)

export default request
