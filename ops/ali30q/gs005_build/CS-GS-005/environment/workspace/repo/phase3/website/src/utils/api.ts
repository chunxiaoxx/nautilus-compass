import axios, { AxiosInstance, AxiosError } from 'axios'
import { tokenUtils } from './token'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenUtils.get()
    if (token && tokenUtils.isValid(token)) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      tokenUtils.remove()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.error || error.response?.data?.message
    if (message) return message

    if (error.response?.status === 401) return '认证失败，请重新登录'
    if (error.response?.status === 403) return '没有权限访问'
    if (error.response?.status === 404) return '请求的资源不存在'
    if (error.response?.status === 500) return '服务器错误，请稍后重试'
    if (error.code === 'ECONNABORTED') return '请求超时，请检查网络连接'
    if (error.code === 'ERR_NETWORK') return '网络错误，请检查网络连接'
  }

  return '发生未知错误，请稍后重试'
}
