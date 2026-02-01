/**
 * 系统管理相关 API（管理员端）
 */
import { get, post, put, del } from '@/utils/request'
import { encryptWithPublicKey } from '@/utils/rsa'
import errorCode from '@/utils/error-code'
import { ElMessage } from 'element-plus'

/**
 * 获取部门列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码（默认1）
 * @param {number} params.per_page - 每页数量（默认20）
 * @returns {Promise<Object>}
 */
export function getDepartments(params = {}) {
  const queryParams = {}
  if (params.page) queryParams.page = params.page
  if (params.per_page) queryParams.per_page = params.per_page

  return get('/api/admin/departments', queryParams)
}

/**
 * 获取部门详情
 * @param {number} deptId - 部门ID
 * @returns {Promise<Object>}
 */
export function getDepartmentDetail(deptId) {
  return get(`/api/admin/departments/${deptId}`)
}

/**
 * 创建部门
 * @param {Object} data - 部门数据
 * @param {string} data.college - 学院
 * @param {string} data.grade - 年级
 * @param {string} data.major - 专业
 * @param {string} data.class_name - 班级名称
 * @param {string} data.bonus_start_date - 加分起始日期（可选，格式：YYYY-MM-DD）
 * @param {number} data.base_score - 部门成员的基础分（可选，默认80）
 * @returns {Promise<Object>}
 */
export function addDepartment(data) {
  return post('/api/admin/departments', data)
}

/**
 * 更新部门信息
 * @param {number} deptId - 部门ID
 * @param {Object} data - 更新数据
 * @param {number} data.base_score - 部门成员的基础分（可选）
 * @returns {Promise<Object>}
 */
export function updateDepartment(deptId, data) {
  return put(`/api/admin/departments/${deptId}`, data)
}

/**
 * 删除部门
 * @param {number} deptId - 部门ID
 * @returns {Promise<Object>}
 */
export function deleteDepartment(deptId) {
  return del(`/api/admin/departments/${deptId}`)
}

/**
 * 为部门绑定证书类型
 * @param {number} deptId - 部门ID
 * @param {Array<number>} certificateTypeIds - 证书类型ID数组
 * @returns {Promise<Object>}
 */
export function bindCertificateTypesToDepartment(deptId, certificateTypeIds) {
  return post(`/api/admin/department/${deptId}/bind-certs`, {
    certificate_type_ids: certificateTypeIds
  })
}

/**
 * 获取证书类型列表
 * @returns {Promise<Object>}
 */
export function getCertTypes() {
  return get('/api/admin/certificate-types')
}

/**
 * 创建证书类型
 * @param {Object} data - 证书类型数据
 * @param {string} data.name - 证书名称
 * @param {string} data.description - 描述（可选）
 * @param {boolean} data.is_required - 是否必填
 * @returns {Promise<Object>}
 */
export function addCertType(data) {
  return post('/api/admin/certificate-types', {
    name: data.name,
    description: data.description || '',
    is_required: data.required !== false // 默认 true
  })
}

/**
 * 删除证书类型
 * @param {number} certTypeId - 证书类型ID
 * @returns {Promise<Object>}
 */
export function deleteCertType(certTypeId) {
  return del(`/api/admin/certificate-types/${certTypeId}`)
}

/**
 * 获取管理员列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码（默认1）
 * @param {number} params.per_page - 每页数量（默认20）
 * @param {string} params.role - 角色筛选（super/normal）
 * @returns {Promise<Object>}
 */
export function getAdmins(params = {}) {
  const queryParams = {}
  if (params.page) queryParams.page = params.page
  if (params.per_page) queryParams.per_page = params.per_page
  if (params.role) queryParams.role = params.role

  return get('/api/admin/admins', queryParams)
}

/**
 * 获取管理员详情
 * @param {number} adminId - 管理员ID
 * @returns {Promise<Object>}
 */
export function getAdminDetail(adminId) {
  return get(`/api/admin/admins/${adminId}`)
}

/**
 * 创建管理员
 * @param {Object} data - 管理员数据
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码（明文，会自动RSA加密）
 * @param {string} data.name - 真实姓名
 * @param {string} data.role - 角色（super/normal）
 * @param {Array<number>} data.department_ids - 管理的部门ID数组（普通管理员必填）
 * @returns {Promise<Object>}
 */
export async function createAdmin(data) {
  // 获取RSA公钥并加密密码
  const { get } = await import('@/utils/request')
  const publicKeyRes = await get('/api/admin/auth/public-key', null, { auth: false })
  const publicKeyPem = publicKeyRes?.public_key
  if (!publicKeyPem) {
    throw new Error('获取公钥失败')
  }

  const encryptedPassword = await encryptWithPublicKey(data.password, publicKeyPem)

  return post('/api/admin/admins', {
    username: data.username,
    password: encryptedPassword,
    name: data.name,
    role: data.role || 'normal',
    department_ids: data.department_ids || []
  })
}

/**
 * 更新管理员信息
 * @param {number} adminId - 管理员ID
 * @param {Object} data - 更新数据
 * @param {string} data.name - 真实姓名（可选）
 * @param {string} data.password - 新密码（可选，明文，会自动RSA加密）
 * @param {string} data.role - 角色（可选，super/normal）
 * @param {Array<number>} data.department_ids - 管理的部门ID数组（可选）
 * @returns {Promise<Object>}
 */
export async function updateAdmin(adminId, data) {
  const updateData = {}

  if (data.name !== undefined) {
    updateData.name = data.name
  }

  if (data.password) {
    // 获取RSA公钥并加密密码
    const { get } = await import('@/utils/request')
    const publicKeyRes = await get('/api/admin/auth/public-key', null, { auth: false })
    const publicKeyPem = publicKeyRes?.public_key
    if (!publicKeyPem) {
      throw new Error('获取公钥失败')
    }

    const encryptedPassword = await encryptWithPublicKey(data.password, publicKeyPem)
    updateData.password = encryptedPassword
  }

  if (data.role !== undefined) {
    updateData.role = data.role
  }

  if (data.department_ids !== undefined) {
    updateData.department_ids = data.department_ids
  }

  return put(`/api/admin/admins/${adminId}`, updateData)
}

/**
 * 删除管理员
 * @param {number} adminId - 管理员ID
 * @returns {Promise<Object>}
 */
export function deleteAdmin(adminId) {
  return del(`/api/admin/admins/${adminId}`)
}

/**
 * 获取系统初始化状态
 * @returns {Promise<Object>} { initialized: boolean }
 */
export function getSystemInitStatus() {
  return get('/api/admin/system/init-status', null, { auth: false })
}

/**
 * 初始化系统（创建首个管理员）
 * @param {Object} data
 * @param {string} data.username
 * @param {string} data.password
 * @param {string} data.name
 */
export async function initializeSystem(data) {
  // 1. 获取公钥
  const publicKeyRes = await get('/api/admin/auth/public-key', null, { auth: false })
  const publicKeyPem = publicKeyRes?.public_key
  if (!publicKeyPem) {
    throw new Error('获取公钥失败')
  }

  // 2. 加密密码
  const encryptedPassword = await encryptWithPublicKey(data.password, publicKeyPem)

  // 3. 提交初始化
  return post('/api/admin/system/initialize', {
    username: data.username,
    password: encryptedPassword,
    name: data.name || 'Super Admin'
  }, { auth: false })
}


