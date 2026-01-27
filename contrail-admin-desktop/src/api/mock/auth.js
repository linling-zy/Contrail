
/**
 * 模拟登录接口
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<Object>}
 */
export function login(username, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (username === 'admin') {
        resolve({
          code: 200,
          data: {
            token: 'mock-super-token',
            role: 'super',
            name: '超级管理员'
          },
          message: '登录成功'
        })
      } else if (username === 'teacher') {
        resolve({
          code: 200,
          data: {
            token: 'mock-normal-token',
            role: 'normal',
            name: '王老师'
          },
          message: '登录成功'
        })
      } else {
        reject({
          code: 401,
          message: '用户名或密码错误'
        })
      }
    }, 500)
  })
}
