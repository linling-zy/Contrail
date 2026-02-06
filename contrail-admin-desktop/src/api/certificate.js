/**
 * 证书审核相关 API（管理员端）
 */
import { get, post } from '@/utils/request'

/**
 * 获取证书列表
 * @param {Object} params - 查询参数
 * @param {number} params.status - 审核状态（0待审/1通过/2驳回）
 * @param {number} params.page - 页码（默认1）
 * @param {number} params.per_page - 每页数量（默认20）
 * @returns {Promise<Object>}
 */
export function getCertificates(params = {}) {
  const queryParams = {}
  
  if (params.status !== undefined && params.status !== '') {
    queryParams.status = params.status
  }
  if (params.page) queryParams.page = params.page
  if (params.per_page) queryParams.per_page = params.per_page
  
  return get('/api/admin/certificates', queryParams)
}

/**
 * 获取证书详情
 * @param {number} certificateId - 证书ID
 * @returns {Promise<Object>}
 */
export function getCertificateDetail(certificateId) {
  return get(`/api/admin/certificates/${certificateId}`)
}

/**
 * 审核证书
 * @param {number} certificateId - 证书ID
 * @param {string} action - 操作类型：'approve' 或 'reject'
 * @param {string} rejectReason - 驳回原因（当 action='reject' 时必填）
 * @returns {Promise<Object>}
 */
export function auditCertificate(certificateId, action, rejectReason = '') {
  const data = {
    action: action
  }
  
  if (action === 'reject' && rejectReason) {
    data.reject_reason = rejectReason
  }
  
  return post(`/api/admin/certificates/${certificateId}/audit`, data)
}





