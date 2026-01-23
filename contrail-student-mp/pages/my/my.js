Page({
    data: {
        userInfo: {
            name: '张三',
            college: '计算机科学与技术学院',
            grade: '2023级',
            major: '软件工程专业',
            class: '2301班',
            studentId: '202300100001'
        },
        paddingTop: 0,
        navBarHeight: 0,
        statusBarHeight: 0
    },

    onLoad() {
        this.initLayout()
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
    }
})
