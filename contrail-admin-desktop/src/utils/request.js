/**
 * HTTP 请求工具
 * 封装 fetch API，提供统一的请求接口
 */

import { ElMessage } from 'element-plus'
import errorCode from '@/utils/error-code'

const baseURL = 'http://127.0.0.1:5000'

/**
 * 获取 Token
 */
function getToken() {
  return localStorage.getItem('token') || ''
}

/**
 * 请求拦截器 - 添加 Token
 */
function getHeaders(customHeaders = {}, skipAuth = false) {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders
  }

  if (!skipAuth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

/**
 * 处理响应
 */
async function handleResponse(response) {
  const contentType = response.headers.get('content-type')
  const isJson = contentType && contentType.includes('application/json')

  let data
  if (isJson) {
    data = await response.json()
  } else {
    data = await response.text()
  }

  if (!response.ok) {
    // 处理错误响应
    const status = response.status
    const message = data.error || data.message || errorCode[status] || `请求失败: ${status}`

    // 显示全局错误提示
    ElMessage.error(message)

    const error = new Error(message)
    error.status = status
    error.data = data
    throw error
  }

  return data
}

/**
 * 通用请求方法
 */
async function request(url, options = {}) {
  const { method = 'GET', data, headers = {}, auth = true, ...restOptions } = options

  const config = {
    method,
    headers: getHeaders(headers, !auth),
    credentials: 'include', // 支持 credentials
    ...restOptions
  }

  // 如果是 POST/PUT/PATCH 请求且有数据，添加到 body
  if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
    config.body = JSON.stringify(data)
  }

  const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`

  try {
    const response = await fetch(fullUrl, config)
    return await handleResponse(response)
  } catch (error) {
    // 网络错误或其他错误
    if (error.status === 401) {
      // Token 过期，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    throw error
  }
}

/**
 * GET 请求
 */
export function get(url, data, options = {}) {
  // 如果有查询参数，拼接到 URL
  if (data && typeof data === 'object') {
    const params = new URLSearchParams(data).toString()
    url = `${url}${params ? `?${params}` : ''}`
  }
  return request(url, { ...options, method: 'GET' })
}

/**
 * POST 请求
 */
export function post(url, data, options = {}) {
  return request(url, { ...options, method: 'POST', data })
}

/**
 * PUT 请求
 */
export function put(url, data, options = {}) {
  return request(url, { ...options, method: 'PUT', data })
}

/**
 * DELETE 请求
 */
export function del(url, options = {}) {
  return request(url, { ...options, method: 'DELETE' })
}

export default {
  get,
  post,
  put,
  delete: del
}


