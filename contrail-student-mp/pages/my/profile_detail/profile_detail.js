const { get } = require('../../../utils/request')

Page({
    data: {
        loading: true,
        userInfo: {},
        steps: []
    },

    onLoad() {
        this.loadProfile()
    },

    async loadProfile() {
        this.setData({ loading: true })
        try {
            const res = await get('/student/profile')
            const userInfo = res.user_info || {}
            const englishScores = res.english_scores || {}
            const achievements = res.achievements || {}
            // View Model Data Transformation

            // 1. English Scores
            const englishSimpleRows = []
            if (englishScores.cet4) englishSimpleRows.push(`CET-4: ${englishScores.cet4}`)
            if (englishScores.cet6) englishSimpleRows.push(`CET-6: ${englishScores.cet6}`)

            const englishComplexRows = (englishScores.ielts || []).map(item => ({
                title: `雅思 (${item.date || ''})`,
                headers: ['总分', '听力', '阅读', '写作', '口语'],
                values: [
                    item.overall || '-',
                    item.listening || '-',
                    item.reading || '-',
                    item.writing || '-',
                    item.speaking || '-'
                ]
            }))

            // 2. Positions
            const posComplexRows = (achievements.positions || []).map(item => {
                // 处理时间范围：优先使用 start_time 和 end_time，如果都没有则显示空
                let timeStr = '';
                if (item.start_time && item.end_time) {
                    timeStr = `${item.start_time} 至 ${item.end_time}`;
                } else if (item.start_time) {
                    timeStr = `${item.start_time} 起`;
                } else if (item.end_time) {
                    timeStr = `至 ${item.end_time}`;
                }

                // 处理集体获奖：可能是数组或字符串
                let tagsStr = '';
                if (item.collective_awards) {
                    if (Array.isArray(item.collective_awards) && item.collective_awards.length > 0) {
                        tagsStr = item.collective_awards.join('、');
                    } else if (typeof item.collective_awards === 'string' && item.collective_awards.trim() && item.collective_awards.trim() !== '无') {
                        tagsStr = item.collective_awards.trim();
                    }
                }

                return {
                    role: item.role || '未填写',
                    organization: item.organization || '',
                    start_time: item.start_time || '',
                    end_time: item.end_time || '',
                    timeStr: timeStr,
                    level: item.level || '',
                    collective_awards: tagsStr
                }
            })

            // 3. Awards
            const awardComplexRows = (achievements.awards || []).map(item => {
                // 构建标题：获奖时间（如果有时间则显示，否则显示奖励名称）
                const title = item.date 
                    ? `获奖时间: ${item.date}`
                    : (item.name || '获奖记录');
                
                // 构建表头和值
                const headers = []
                const values = []
                
                // 奖励名称（始终显示，因为这是核心信息）
                headers.push('奖励名称')
                values.push(item.name || '未知奖项')
                
                // 奖励级别
                if (item.level) {
                    headers.push('级别')
                    values.push(item.level)
                }
                
                // 获奖等次（优先使用 rank，兼容 grade）
                const rank = item.rank || item.grade
                if (rank) {
                    headers.push('等次')
                    values.push(rank)
                }
                
                // 主办单位
                if (item.organizer) {
                    headers.push('主办单位')
                    values.push(item.organizer)
                }
                
                return {
                    title: title,
                    headers: headers.length > 0 ? headers : ['暂无信息'],
                    values: values.length > 0 ? values : ['-']
                }
            })

            this.setData({
                userInfo: {
                    name: userInfo.name || '未设置',
                    studentId: userInfo.student_id || '未设置',
                    // Mask ID Card: 123456********1234
                    idCard: userInfo.id_card_no ? userInfo.id_card_no.replace(/^(.{6})(?:\d+)(.{4})$/, "$1********$2") : '未设置',
                    phone: userInfo.phone || '未设置',
                    birthplace: userInfo.birthplace || '未设置',
                    ethnicity: userInfo.ethnicity || '未设置',
                    politicalAffiliation: userInfo.political_affiliation || '未设置',
                    gender: userInfo.gender || '未设置',
                    birthDate: userInfo.birth_date || '未设置',

                    college: userInfo.college || '未设置',
                    grade: userInfo.grade || '未设置',
                    major: userInfo.major || '未设置',
                    class: userInfo.class_name || '未设置',

                    credits: userInfo.credits || '0',
                    gpa: userInfo.gpa || '0.0',
                    baseScore: userInfo.base_score || '0',
                    comprehensiveScore: userInfo.total_score || '0'
                },
                viewData: {
                    english: {
                        simple: englishSimpleRows,
                        complex: englishComplexRows
                    },
                    positions: {
                        complex: posComplexRows
                    },
                    awards: {
                        complex: awardComplexRows
                    }
                }
            })
        } catch (err) {
            wx.showToast({ title: '加载失败', icon: 'none' })
            console.error(err)
        } finally {
            this.setData({ loading: false })
        }
    }
})
