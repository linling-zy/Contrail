

const mockStudents = Array.from({ length: 200 }).map((_, index) => {
    // 简单的班级分配逻辑
    const classId = [101, 102, 103, 104][index % 4]
    const classIds = { 101: '机械241', 102: '机械242', 103: '飞行2301', 104: '飞行2302' }
    return {
        id: index + 1,
        studentNo: `2024${classId}${String(index + 1).padStart(5, '0')}`, // 12位学号: 年份(4)+班级(3)+序号(5)
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
        },
        teacherEvaluation: "该生在校表现良好，积极参与班级活动。",
        certificates: [
            { id: 1, name: '大学英语四级', status: 'obtained', date: '2024-06-20' },
            { id: 2, name: '计算机二级', status: 'pending', date: '2024-09-10' },
            { id: 3, name: '普通话水平测试', status: 'obtained', date: '2024-05-15' },
            { id: 4, name: '心理健康教育', status: 'obtained', date: '2024-04-10' }
        ]
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

/**
 * 更新学生档案信息（包括评价等）
 * @param {Number} id 
 * @param {Object} data 
 */
export function updateStudentProfile(id, data) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            const student = mockStudents.find(s => s.id === id)
            if (student) {
                if (data.status) {
                    student.status = { ...student.status, ...data.status }
                    delete data.status
                }
                Object.assign(student, data)
                resolve({ code: 200, message: '档案信息更新成功' })
            } else {
                reject({ code: 404, message: '未找到学生' })
            }
        }, 300)
    })
}

/**
 * 获取学生积分流水
 * @param {Number} id
 */
export function getStudentScoreLogs(id) {
    return new Promise((resolve) => {
        setTimeout(() => {
            // 生成模拟数据
            const logs = [
                { id: 101, delta: 2, reason: '全勤奖励', type: 'system', createTime: '2024-03-01 08:00:00' },
                { id: 102, delta: -5, reason: '宿舍卫生不合格', type: 'manual', createTime: '2024-03-05 14:30:00' },
                { id: 103, delta: 1, reason: '积极回答问题', type: 'manual', createTime: '2024-03-06 10:15:00' },
                { id: 104, delta: 3, reason: '参与志愿服务', type: 'system', createTime: '2024-03-10 09:00:00' },
                { id: 105, delta: -2, reason: '早操迟到', type: 'manual', createTime: '2024-03-12 06:40:00' },
                { id: 106, delta: 5, reason: '获得校级荣誉', type: 'manual', createTime: '2024-03-15 16:00:00' },
                { id: 107, delta: 1, reason: '按时提交作业', type: 'system', createTime: '2024-03-18 12:00:00' }
            ]

            resolve({
                code: 200,
                data: logs
            })
        }, 300)
    })
}

// 模拟导出任务存储
const exportTasks = {}

/**
 * 发起导出任务
 * @param {Number} classId 
 */
export function startExportTask(classId) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const taskId = 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
            exportTasks[taskId] = {
                status: 'processing',
                progress: 0,
                total: 100, // 假定100个进度点
                createTime: Date.now()
            }

            // 模拟后台异步处理
            simulateExportProcess(taskId)

            resolve({
                code: 200,
                data: { taskId }
            })
        }, 500)
    })
}

/**
 * 模拟导出进度更新
 */
function simulateExportProcess(taskId) {
    const task = exportTasks[taskId]
    if (!task) return

    const timer = setInterval(() => {
        if (task.progress >= 100) {
            clearInterval(timer)
            task.status = 'completed'
            task.download_url = `http://mock-api/download/${taskId}.zip` // 模拟下载链接
            return
        }
        // 随机增加进度
        task.progress += Math.floor(Math.random() * 10) + 5
        if (task.progress > 100) task.progress = 100
    }, 800)
}

/**
 * 查询导出任务进度
 * @param {String} taskId 
 */
export function getExportTaskStatus(taskId) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            const task = exportTasks[taskId]
            if (task) {
                resolve({
                    code: 200,
                    data: { ...task }
                })
            } else {
                reject({ code: 404, message: '任务不存在' })
            }
        }, 300)
    })
}

/**
 * 模拟文件上传（批量导入）
 * @param {FormData} formData 
 */
export function uploadStudentFile(formData) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // 简单的校验
            if (!formData) {
                reject({ code: 400, message: '文件不能为空' })
                return
            }
            resolve({
                code: 200,
                message: '导入成功',
                data: {
                    successCount: 45,
                    failCount: 0
                }
            })
        }, 1500)
    })
}
