const { get } = require('../../utils/request')

Page({
    data: {
        userInfo: {
            name: '',
            college: '',
            grade: '',
            major: '',
            class: '',
            studentId: ''
        },
        paddingTop: 0,
        navBarHeight: 0,
        statusBarHeight: 0,
        isLoading: false,
    },

    onLoad() {
        this.initLayout()
        this.loadUserInfo()
    },

    onShow() {
        // 每次显示页面时刷新用户信息（可能在其他页面修改了信息）
        this.loadUserInfo()
    },

    initLayout() {
        const menuButtonInfo = wx.getMenuButtonBoundingClientRect()
        const windowInfo = wx.getWindowInfo()

        const statusBarHeight = windowInfo.statusBarHeight || windowInfo.safeArea?.top || 0
        const menuButtonHeight = menuButtonInfo.height || 32
        const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonHeight
        const totalTop = statusBarHeight + navBarHeight

        this.setData({
            paddingTop: totalTop,
            navBarHeight: navBarHeight,
            statusBarHeight: statusBarHeight
        })
    },

    /**
     * 从后端API加载用户信息
     * 接口: GET /api/auth/profile
     * 返回: { user: { id, name, student_id, college, grade, major, class_name, ... } }
     */
    async loadUserInfo() {
        this.setData({ isLoading: true })
        try {
            const res = await get('/auth/profile')
            // 后端返回: { user: {...} }
            const user = res.user || {}
            
            // 映射后端字段到前端显示字段
            this.setData({
                userInfo: {
                    name: user.name || '',
                    college: user.college || '',
                    grade: user.grade || '',
                    major: user.major || '',
                    class: user.class_name || '',
                    studentId: user.student_id || '',
                }
            })
        } catch (err) {
            console.error('加载用户信息失败:', err)
            wx.showToast({
                title: err.message || '加载失败，请稍后重试',
                icon: 'none',
                duration: 2000,
            })
        } finally {
            this.setData({ isLoading: false })
        }
    },
})
