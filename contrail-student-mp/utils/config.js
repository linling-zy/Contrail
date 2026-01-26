// 统一域名/环境配置
// 注意：真机/小程序后台需要把该域名加入“request合法域名”
// 开发时可按需改成你的局域网后端地址，例如：http://192.168.1.10:5000

const DEFAULT_BASE_URL = 'http://127.0.0.1:5000'
const API_PREFIX = '/api'

function getBaseURL() {
  // 允许通过本地存储覆盖（方便不同同学本地调试）
  const override = wx.getStorageSync('baseURL')
  return override || DEFAULT_BASE_URL
}

module.exports = {
  API_PREFIX,
  getBaseURL,
}


