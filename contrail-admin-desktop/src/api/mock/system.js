

// 模拟初始部门数据 (扁平化，仅一级班级)
const departments = [
    { id: 101, name: '民航与航空学院2023级机械241班', studentCount: 45 },
    { id: 102, name: '民航与航空学院2023级机械242班', studentCount: 42 },
    { id: 103, name: '飞行技术学院2023级飞行2301班', studentCount: 30 },
    { id: 104, name: '飞行技术学院2023级飞行2302班', studentCount: 28 }
]

// 模拟证书类型
let certTypes = [
    { id: 1, name: '大学英语四级 (CET-4)', required: true },
    { id: 2, name: '大学英语六级 (CET-6)', required: false },
    { id: 3, name: '年度体检表', required: true },
    { id: 4, name: '政审材料', required: true }
]

// 模拟管理员
let admins = [
    { id: 1, username: 'admin', name: '超级管理员', role: 'super', deptId: null },
    { id: 2, username: 'teacher', name: '王老师', role: 'normal', deptId: 101 }
]

export function getDepartments() {
    return Promise.resolve({ code: 200, data: departments })
}

export function getCertTypes() {
    return Promise.resolve({ code: 200, data: certTypes })
}

// 模拟保存（针对扁平化结构简化）
export function saveClassCerts(classId, certIds) {
    return new Promise(resolve => {
        setTimeout(() => {
            const cls = departments.find(d => d.id === classId)
            if (cls) {
                cls.boundCerts = certIds
                resolve({ code: 200, message: '配置已保存' })
            } else {
                resolve({ code: 404, message: '班级未找到' })
            }
        }, 300)
    })
}

export function getAdmins() {
    return Promise.resolve({ code: 200, data: admins })
}

export function addDepartment(data) {
    return new Promise(resolve => {
        setTimeout(() => {
            const newId = departments.length ? Math.max(...departments.map(d => d.id)) + 1 : 101
            departments.push({
                id: newId,
                name: data.name,
                studentCount: 0
            })
            resolve({ code: 200, message: '添加成功' })
        }, 300)
    })
}
