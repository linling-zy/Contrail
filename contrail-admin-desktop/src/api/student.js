/**
 * 学生相关 API
 */
import { get, post, put } from '@/utils/request'

/**
 * 获取学生列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码（默认1）
 * @param {number} params.per_page - 每页数量（默认20）
 * @param {number} params.department_id - 部门ID（可选）
 * @param {string} params.filter - 筛选类型（name/student_id/class_name）
 * @param {string} params.keyword - 筛选关键词
 * @param {string} params.status_stage - 阶段状态（preliminary/medical/political/admission）
 * @param {string} params.status_value - 状态值（pending/qualified/unqualified）
 * @returns {Promise<Object>}
 */
export function getStudents(params = {}) {
  // 构建查询参数
  const queryParams = {}
  
  if (params.page) queryParams.page = params.page
  if (params.per_page) queryParams.per_page = params.per_page
  if (params.department_id) queryParams.department_id = params.department_id
  if (params.filter) queryParams.filter = params.filter
  if (params.keyword) queryParams.keyword = params.keyword
  if (params.status_stage) queryParams.status_stage = params.status_stage
  if (params.status_value) queryParams.status_value = params.status_value
  
  // 兼容旧的 classId 参数，转换为 department_id
  if (params.classId && !params.department_id) {
    queryParams.department_id = params.classId
  }
  
  return get('/api/admin/students', queryParams)
}

/**
 * 获取学生详情
 * @param {number} studentId - 学生ID
 * @returns {Promise<Object>}
 */
export function getStudentDetail(studentId) {
  return get(`/api/admin/students/${studentId}`)
}

/**
 * 更新学生状态
 * @param {number} studentId - 学生ID
 * @param {Object} statusObj - 状态对象
 * @returns {Promise<Object>}
 */
export function updateStudentStatus(studentId, statusObj) {
  return put(`/api/admin/students/${studentId}/status`, statusObj)
}

/**
 * 更新学生档案（聚合更新）
 * @param {number} studentId - 学生ID
 * @param {Object} data - 档案数据
 * @param {Object} data.base_info - 基本信息 { name, student_id, department_id, base_score }
 * @param {Object} data.process_status - 阶段状态 { preliminary, medical, political, admission }
 * @param {string} data.new_comment - 新评语内容（可选）
 * @returns {Promise<Object>}
 */
export function updateStudentProfile(studentId, data) {
  return put(`/api/admin/students/${studentId}/archive`, data)
}

/**
 * 获取学生积分流水
 * @param {number} studentId - 学生ID
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码（默认1）
 * @param {number} params.limit - 每页数量（默认20）
 * @param {number} params.type - 类型过滤（1-人工调整, 2-系统自动）
 * @returns {Promise<Object>}
 */
export function getStudentScoreLogs(studentId, params = {}) {
  const queryParams = {}
  if (params.page) queryParams.page = params.page
  if (params.limit) queryParams.limit = params.limit
  if (params.type) queryParams.type = params.type
  
  return get(`/api/admin/students/${studentId}/score-logs`, queryParams)
}

/**
 * 调整学生积分
 * @param {number} userId - 学生ID
 * @param {number} delta - 变动分数（正数为加分，负数为扣分）
 * @param {string} reason - 变动原因
 * @returns {Promise<Object>}
 */
export function adjustStudentScore(userId, delta, reason) {
  return post('/api/admin/score/adjust', {
    user_id: userId,
    delta: delta,
    reason: reason
  })
}

/**
 * 添加学生评语
 * @param {number} studentId - 学生ID
 * @param {string} content - 评语内容
 * @returns {Promise<Object>}
 */
export function addStudentComment(studentId, content) {
  return post(`/api/admin/students/${studentId}/comment`, {
    content: content
  })
}

/**
 * 批量导入学生
 * @param {FormData} formData - 包含 Excel 文件的 FormData，必须包含 department_id 字段
 * @param {number} departmentId - 部门ID（可选，如果formData中已有则不需要）
 * @returns {Promise<Object>}
 */
export function importStudents(formData, departmentId = null) {
  const token = localStorage.getItem('token') || ''
  
  // 如果提供了 departmentId 参数且 formData 中没有，则添加到 formData
  if (departmentId && !formData.has('department_id')) {
    formData.append('department_id', departmentId.toString())
  }
  
  return fetch('http://127.0.0.1:5000/api/admin/students/import', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // 注意：不要设置 Content-Type，让浏览器自动设置 multipart/form-data 边界
    },
    credentials: 'include',
    body: formData
  }).then(async (response) => {
    const data = await response.json()
    if (!response.ok) {
      const error = new Error(data.message || `导入失败: ${response.status}`)
      error.data = data
      throw error
    }
    return data
  })
}

/**
 * 发起部门学生档案导出任务
 * @param {number} deptId - 部门ID
 * @returns {Promise<Object>}
 */
export function startExportTask(deptId) {
  return post(`/api/admin/department/${deptId}/export/start`)
}

/**
 * 查询导出任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>}
 */
export function getExportTaskStatus(taskId) {
  return get(`/api/admin/export/status/${taskId}`)
}

/**
 * 下载导出文件
 * @param {string} taskId - 任务ID
 * @returns {Promise<Blob>}
 */
export function downloadExportFile(taskId) {
  const token = localStorage.getItem('token') || ''
  
  return fetch(`http://127.0.0.1:5000/api/admin/export/download/${taskId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    credentials: 'include'
  }).then(async (response) => {
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || `下载失败: ${response.status}`)
    }
    return response.blob()
  })
}

