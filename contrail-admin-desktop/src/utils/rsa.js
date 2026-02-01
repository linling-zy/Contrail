/**
 * RSA 加密工具
 * 使用 JSEncrypt 库进行 RSA 公钥加密
 */

// JSEncrypt 类缓存
let JSEncryptClass = null
let loadingPromise = null

/**
 * 加载 JSEncrypt 库
 * 优先尝试从 npm 包导入，失败则从 CDN 加载
 */
async function loadJSEncrypt() {
  if (JSEncryptClass) {
    return JSEncryptClass
  }

  if (loadingPromise) {
    return loadingPromise
  }

  loadingPromise = (async () => {
    try {
      // 尝试从 npm 包导入
      const module = await import('jsencrypt')
      JSEncryptClass = module.default || module.JSEncrypt || module
      if (JSEncryptClass) {
        return JSEncryptClass
      }
    } catch (e) {
      console.warn('无法从 npm 包加载 jsencrypt，尝试从 CDN 加载:', e.message)
    }

    // 如果 npm 包导入失败，从 CDN 加载
    if (typeof window !== 'undefined') {
      if (window.JSEncrypt) {
        JSEncryptClass = window.JSEncrypt
        return JSEncryptClass
      }

      // 动态加载 CDN 脚本
      return new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/npm/jsencrypt@3.3.2/bin/jsencrypt.min.js'
        script.onload = () => {
          JSEncryptClass = window.JSEncrypt
          if (JSEncryptClass) {
            resolve(JSEncryptClass)
          } else {
            reject(new Error('CDN 加载失败：未找到 JSEncrypt'))
          }
        }
        script.onerror = () => {
          reject(new Error('无法从 CDN 加载 JSEncrypt 库'))
        }
        document.head.appendChild(script)
      })
    }

    throw new Error('无法加载 JSEncrypt 库：当前环境不支持')
  })()

  return loadingPromise
}

/**
 * 获取 JSEncrypt 实例
 */
async function getJSEncryptInstance() {
  const JSEncrypt = await loadJSEncrypt()
  return new JSEncrypt()
}

/**
 * 使用 RSA 公钥加密文本
 * @param {string} plainText - 要加密的明文
 * @param {string} publicKeyPem - PEM 格式的公钥
 * @returns {Promise<string>} - Base64 编码的加密结果
 */
export async function encryptWithPublicKey(plainText, publicKeyPem) {
  if (!plainText) {
    throw new Error('密码不能为空')
  }
  if (!publicKeyPem) {
    throw new Error('公钥不能为空')
  }
  
  const encrypt = await getJSEncryptInstance()
  
  // 设置公钥
  encrypt.setPublicKey(publicKeyPem)
  
  // 加密
  const encrypted = encrypt.encrypt(String(plainText))
  
  if (!encrypted) {
    throw new Error('RSA 加密失败，请检查公钥格式是否正确')
  }
  
  return encrypted
}

