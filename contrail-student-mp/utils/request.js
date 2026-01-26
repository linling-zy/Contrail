const { getBaseURL, API_PREFIX } = require('./config')

function isAbsoluteUrl(url) {
  return /^https?:\/\//i.test(url)
}

function joinUrl(baseURL, path) {
  if (isAbsoluteUrl(path)) return path
  const base = baseURL.replace(/\/+$/, '')
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${API_PREFIX}${p}`
}

function extractBizCode(resData) {
  // 兼容两种风格：
  // 1) 后端按HTTP状态码 + {access_token,user}/{error}
  // 2) 文档里提到的 {code:200,data:{...}}
  if (!resData || typeof resData !== 'object') return null
  if (typeof resData.code === 'number') return resData.code
  return null
}

function extractMessage(resData, fallback) {
  if (!resData || typeof resData !== 'object') return fallback
  return resData.error || resData.message || resData.msg || fallback
}

function redirectToLogin() {
  try {
    wx.removeStorageSync('token')
    wx.removeStorageSync('user')
  } catch (e) {}

  const pages = getCurrentPages()
  const current = pages && pages.length ? pages[pages.length - 1].route : ''
  if (current === 'pages/login/login') return

  wx.reLaunch({ url: '/pages/login/login' })
}

/**
 * 统一网络请求封装
 * @param {Object} options
 * @param {string} options.url - 例如 '/auth/login'（自动拼接 baseURL + '/api'）
 * @param {string} [options.method]
 * @param {Object} [options.data]
 * @param {Object} [options.header]
 * @param {boolean} [options.auth] - 是否自动带 token，默认 true
 * @param {number} [options.timeout]
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data,
    header = {},
    auth = true,
    timeout = 15000,
  } = options || {}

  if (!url) {
    return Promise.reject(new Error('request: url 不能为空'))
  }

  const fullUrl = joinUrl(getBaseURL(), url)
  const token = wx.getStorageSync('token')

  const finalHeader = {
    'Content-Type': 'application/json',
    ...header,
  }

  if (auth && token) {
    finalHeader.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: fullUrl,
      method,
      data,
      header: finalHeader,
      timeout,
      success: (res) => {
        const { statusCode, data: resData } = res || {}

        // 先处理“业务code”风格（如 api.md 提到的 code:200）
        const bizCode = extractBizCode(resData)
        if (bizCode !== null) {
          if (bizCode === 200) return resolve(resData.data)
          if (bizCode === 401) {
            redirectToLogin()
            return reject(new Error(extractMessage(resData, '登录已过期，请重新登录')))
          }
          return reject(new Error(extractMessage(resData, `请求失败(${bizCode})`)))
        }

        // 再处理“HTTP状态码”风格（本项目后端实际实现）
        if (statusCode >= 200 && statusCode < 300) {
          return resolve(resData)
        }

        if (statusCode === 401) {
          // 登录接口本身返回 401：只提示，不重定向（避免死循环）
          if (String(url).includes('/auth/login')) {
            return reject(new Error(extractMessage(resData, '身份证号或密码错误')))
          }
          redirectToLogin()
          return reject(new Error(extractMessage(resData, '登录已过期，请重新登录')))
        }

        return reject(new Error(extractMessage(resData, `请求失败(${statusCode})`)))
      },
      fail: (err) => {
        const msg = (err && err.errMsg) || '网络异常，请稍后重试'
        reject(new Error(msg))
      },
    })
  })
}

function get(url, data, options) {
  return request({ url, method: 'GET', data, ...(options || {}) })
}
function post(url, data, options) {
  return request({ url, method: 'POST', data, ...(options || {}) })
}
function put(url, data, options) {
  return request({ url, method: 'PUT', data, ...(options || {}) })
}
function del(url, data, options) {
  return request({ url, method: 'DELETE', data, ...(options || {}) })
}

function uploadFile(options) {
  const {
    url,
    filePath,
    name = 'file',
    formData,
    header = {},
    auth = true,
  } = options || {}

  if (!url) return Promise.reject(new Error('uploadFile: url 不能为空'))
  if (!filePath) return Promise.reject(new Error('uploadFile: filePath 不能为空'))

  const fullUrl = joinUrl(getBaseURL(), url)
  const token = wx.getStorageSync('token')
  const finalHeader = { ...header }
  if (auth && token) {
    finalHeader.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: fullUrl,
      filePath,
      name,
      formData,
      header: finalHeader,
      success: (res) => {
        let resData = res.data
        try {
          resData = JSON.parse(res.data)
        } catch (e) {}

        // 先处理业务 code 风格（如后端返回 {code: 200, msg: "...", data: {...}}）
        const bizCode = extractBizCode(resData)
        if (bizCode !== null) {
          if (bizCode === 200) return resolve(resData.data || resData)
          if (bizCode === 401) {
            redirectToLogin()
            return reject(new Error(extractMessage(resData, '登录已过期，请重新登录')))
          }
          return reject(new Error(extractMessage(resData, `上传失败(${bizCode})`)))
        }

        // 再处理 HTTP 状态码风格
        if (res.statusCode >= 200 && res.statusCode < 300) {
          return resolve(resData)
        }
        if (res.statusCode === 401) {
          redirectToLogin()
          return reject(new Error(extractMessage(resData, '登录已过期，请重新登录')))
        }
        return reject(new Error(extractMessage(resData, `上传失败(${res.statusCode})`)))
      },
      fail: (err) => reject(new Error((err && err.errMsg) || '上传失败')),
    })
  })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  uploadFile,
}


