let JSEncryptModule
try {
  // 优先使用 vendor 版（已放入源码，避免 node_modules/miniprogram_npm 解析差异）
  JSEncryptModule = require('./jsencrypt.vendor.min')
} catch (e) {
  try {
    // 兜底：若你在开发者工具里“构建 npm”，也可走 miniprogram_npm
    JSEncryptModule = require('../miniprogram_npm/jsencrypt/index')
  } catch (e2) {
    throw new Error('缺少 RSA 加密依赖：请确认存在 utils/jsencrypt.vendor.min.js，或在开发者工具执行“工具→构建 npm”。')
  }
}

const JSEncrypt = (JSEncryptModule && (JSEncryptModule.JSEncrypt || JSEncryptModule)) || null

function encryptWithPublicKey(plainText, publicKeyPem) {
  if (!plainText) throw new Error('密码不能为空')
  if (!publicKeyPem) throw new Error('publicKey 为空')
  if (!JSEncrypt) throw new Error('RSA加密模块初始化失败')

  const enc = new JSEncrypt()
  enc.setPublicKey(publicKeyPem)
  const encrypted = enc.encrypt(String(plainText))
  if (!encrypted) throw new Error('RSA加密失败')
  return encrypted
}

module.exports = {
  encryptWithPublicKey,
}


