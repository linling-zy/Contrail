

const mockStudents = Array.from({ length: 50 }).map((_, index) => {
    // 简单的班级分配逻辑
    const classId = [101, 102, 103, 104][index % 4]
    const classIds = { 101: '机械241', 102: '机械242', 103: '飞行2301', 104: '飞行2302' }
    return {
        id: index + 1,
        name: `学生${index + 1}`,
        idCard: `51010020000101${String(index).padStart(4, '0')}`,
        college: classId > 102 ? '飞行技术学院' : '民航与航空学院',
        classId: classId,
        className: classIds[classId],
        totalScore: 90 + Math.floor(Math.random() * 20), // 90-110
        status: {
            preliminary: Math.random() > 0.1 ? 'qualified' : 'failed',
            medical: Math.random() > 0.3 ? (Math.random() > 0.5 ? 'qualified' : 'pending') : 'failed',
            political: 'pending',
            admission: 'pending'
        }
    }
})

/**
 * 获取学生列表
 */
export function getStudents(params) {
    return new Promise((resolve) => {
        setTimeout(() => {
            let list = [...mockStudents]
            if (params.classId) {
                list = list.filter(item => item.classId === Number(params.classId))
            }
            if (params.name) {
                list = list.filter(item => item.name.includes(params.name) || item.idCard.includes(params.name))
            }
            resolve({
                code: 200,
                data: {
                    list,
                    total: list.length
                }
            })
        }, 300)
    })
}

/**
 * 更新学生状态
 * @param {Number} id 
 * @param {Object} statusObj 
 */
export function updateStudentStatus(id, statusObj) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            const student = mockStudents.find(s => s.id === id)
            if (student) {
                student.status = { ...student.status, ...statusObj }
                resolve({ code: 200, message: '状态更新成功' })
            } else {
                reject({ code: 404, message: '未找到学生' })
            }
        }, 300)
    })
}

/**
 * 更新积分
 * @param {Number} id 
 * @param {Number} value 
 * @param {String} reason 
 */
export function updateStudentScore(id, value, reason) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            const student = mockStudents.find(s => s.id === id)
            if (student) {
                student.totalScore += Number(value)
                resolve({ code: 200, message: `积分已更新: ${value > 0 ? '+' : ''}${value} (原因: ${reason})` })
            } else {
                reject({ code: 404, message: '未找到学生' })
            }
        }, 300)
    })
}
