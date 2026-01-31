

// 模拟初始部门数据 (扁平化，仅一级班级)
// 模拟初始部门数据 (扁平化，仅一级班级)
const departments = [
    {
        id: 101,
        name: '民航与航空学院2023级机械241班',
        studentCount: 45,
        college: '民航与航空学院',
        grade: '2023级',
        major: '机械',
        className: '241班',
        autoScoreTime: '',
        boundCerts: []
    },
    {
        id: 102,
        name: '民航与航空学院2023级机械242班',
        studentCount: 42,
        college: '民航与航空学院',
        grade: '2023级',
        major: '机械',
        className: '242班',
        autoScoreTime: '',
        boundCerts: []
    },
    {
        id: 103,
        name: '飞行技术学院2023级飞行2301班',
        studentCount: 30,
        college: '飞行技术学院',
        grade: '2023级',
        major: '飞行技术',
        className: '2301班',
        autoScoreTime: '',
        boundCerts: []
    },
    {
        id: 104,
        name: '飞行技术学院2023级飞行2302班',
        studentCount: 28,
        college: '飞行技术学院',
        grade: '2023级',
        major: '飞行技术',
        className: '2302班',
        autoScoreTime: '',
        boundCerts: []
    }
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

export function getDepartmentDetail(id) {
    return new Promise(resolve => {
        const dept = departments.find(d => d.id === Number(id))
        resolve({ code: 200, data: dept || {} })
    })
}

export function updateDepartment(data) {
    return new Promise(resolve => {
        setTimeout(() => {
            const index = departments.findIndex(d => d.id === data.id)
            if (index !== -1) {
                // Merge updates
                departments[index] = { ...departments[index], ...data }
                // Reconstruct full name if parts are present
                const d = departments[index]
                if (d.college && d.grade && d.major && d.className) {
                    d.name = `${d.college}${d.grade}${d.major}${d.className}`
                }
                resolve({ code: 200, message: '更新成功' })
            } else {
                resolve({ code: 404, message: '部门未找到' })
            }
        }, 300)
    })
}


export function getAdmins() {
    return Promise.resolve({ code: 200, data: admins })
}

export function createAdmin(data) {
    return new Promise(resolve => {
        setTimeout(() => {
            const newId = admins.length ? Math.max(...admins.map(a => a.id)) + 1 : 1
            admins.push({
                id: newId,
                ...data
            })
            resolve({ code: 200, message: '管理员创建成功' })
        }, 300)
    })
}

export function updateAdmin(data) {
    return new Promise(resolve => {
        setTimeout(() => {
            const index = admins.findIndex(a => a.id === data.id)
            if (index !== -1) {
                admins[index] = { ...admins[index], ...data }
                resolve({ code: 200, message: '更新成功' })
            } else {
                resolve({ code: 404, message: '管理员未找到' })
            }
        }, 300)
    })
}

export function deleteAdmin(id) {
    return new Promise(resolve => {
        setTimeout(() => {
            admins = admins.filter(a => a.id !== id)
            resolve({ code: 200, message: '删除成功' })
        }, 300)
    })
}

export function getCertTypes() {
    return Promise.resolve({ code: 200, data: certTypes })
}

export function addCertType(data) {
    return new Promise(resolve => {
        setTimeout(() => {
            const newId = certTypes.length ? Math.max(...certTypes.map(c => c.id)) + 1 : 1
            certTypes.push({
                id: newId,
                name: data.name,
                required: data.required
            })
            resolve({ code: 200, message: '添加成功' })
        }, 300)
    })
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
