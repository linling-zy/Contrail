
// 模拟证书数据
const mockData = Array.from({ length: 10 }).map((_, index) => ({
    id: index + 1,
    studentName: index % 2 === 0 ? '张三' : '李四',
    className: '飞行2301',
    certName: index % 3 === 0 ? '英语四级' : '计算机二级',
    status: index < 3 ? 0 : (index < 7 ? 1 : 2), // 0:待审, 1:通过, 2:驳回
    statusText: '', // Will be handled by frontend mapping usually, but sticking to basic data here
    imgUrl: 'https://fuss10.elemecdn.com/e/5d/4a731a90594a4af544c0c25941171jpeg.jpeg', // Element Plus example image
    uploadTime: `2024-05-${10 + index} 14:00:00`,
    rejectReason: index >= 7 ? '图片模糊' : ''
}))

/**
 * 获取证书列表
 * @param {Object} params { status }
 */
export function getCertificates(params) {
    return new Promise((resolve) => {
        setTimeout(() => {
            let list = [...mockData]
            if (params && params.status !== undefined && params.status !== '') {
                list = list.filter(item => item.status === Number(params.status))
            }
            resolve({
                code: 200,
                data: {
                    list,
                    total: list.length
                },
                message: '获取成功'
            })
        }, 300)
    })
}

/**
 * 更新审核状态
 * @param {Number} id 
 * @param {Number} status 
 * @param {String} reason 
 */
export function updateStatus(id, status, reason = '') {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            const item = mockData.find(i => i.id === id)
            if (item) {
                item.status = status
                item.rejectReason = reason
                resolve({
                    code: 200,
                    message: '操作成功'
                })
            } else {
                reject({
                    code: 404,
                    message: '未找到记录'
                })
            }
        }, 300)
    })
}
