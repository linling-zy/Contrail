
// 模拟初始部门数据 (学院 -> 年级 -> 专业 -> 班级)
const departments = [
    {
        id: 1,
        name: '飞行技术学院',
        code: 'F01',
        level: 1, // 学院
        children: [
            {
                id: 11,
                name: '2023级',
                level: 2, // 年级
                children: [
                    {
                        id: 111,
                        name: '飞行技术专业',
                        level: 3, // 专业
                        children: [
                            { id: 1111, name: '飞行2301', level: 4, boundCerts: [1, 2] }, // 班级, boundCerts是证书类型ID
                            { id: 1112, name: '飞行2302', level: 4, boundCerts: [1] }
                        ]
                    }
                ]
            }
        ]
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
    { id: 2, username: 'teacher', name: '王老师', role: 'normal', deptId: 1111 }
]

export function getDepartments() {
    return Promise.resolve({ code: 200, data: departments })
}

export function getCertTypes() {
    return Promise.resolve({ code: 200, data: certTypes })
}

// 模拟保存（需递归查找并更新，这里简化处理只针对 F2301, F2302）
export function saveClassCerts(classId, certIds) {
    return new Promise(resolve => {
        setTimeout(() => {
            // 深度遍历查找更新 (Simplified for mock: We assume we find it)
            const findAndUpdate = (list) => {
                for (const item of list) {
                    if (item.id === classId) {
                        item.boundCerts = certIds
                        return true
                    }
                    if (item.children) {
                        if (findAndUpdate(item.children)) return true
                    }
                }
                return false
            }
            findAndUpdate(departments)
            resolve({ code: 200, message: '配置已保存' })
        }, 300)
    })
}

export function getAdmins() {
    return Promise.resolve({ code: 200, data: admins })
}
