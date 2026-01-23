const app = getApp()

Page({
    data: {
        paddingTop: 0,
        scrollViewHeight: 0,
        certificates: [], // Certificate list
    },

    onLoad() {
        this.initLayout()
        this.loadMockData()
    },

    // Calculate layout safe area for custom navigation bar
    initLayout() {
        const menuButtonInfo = wx.getMenuButtonBoundingClientRect()
        const windowInfo = wx.getWindowInfo()

        const statusBarHeight = windowInfo.statusBarHeight || windowInfo.safeArea?.top || 0
        const menuButtonHeight = menuButtonInfo.height || 32
        // Calculate the space from status bar to menu button bottom
        const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonHeight
        // Total top space needed: status bar + nav bar
        const totalTop = statusBarHeight + navBarHeight

        // Calculate scroll view height: windowHeight - totalTop - tabBarHeight (approx 48px + safe area bottom)
        // Actually for custom nav, the page takes full height. 
        // We want the scroll view to fill the rest of the screen.
        // However, since it is a tab bar page, the tab bar exists.
        // We need to verify if we definitely know the tab bar height. 
        // Standard tab bar is ~50px + safe area.
        const safeAreaBottom = windowInfo.safeArea ? (windowInfo.screenHeight - windowInfo.safeArea.bottom) : 0
        const tabBarHeight = 48 + safeAreaBottom // Approximate

        const scrollViewHeight = windowInfo.windowHeight - totalTop - tabBarHeight

        this.setData({
            paddingTop: totalTop,
            scrollViewHeight: scrollViewHeight,
            navBarHeight: navBarHeight,
            statusBarHeight: statusBarHeight
        })
    },

    loadMockData() {
        const mockData = [
            {
                id: 1,
                title: '英语六级证书',
                thumb: '', // Empty for default icon
                status: 'passed',
                statusLabel: '已通过'
            },
            {
                id: 2,
                title: '计算机二级证书',
                thumb: '',
                status: 'auditing',
                statusLabel: '审核中'
            },
            {
                id: 3,
                title: '普通话一级乙等',
                thumb: '',
                status: 'rejected',
                statusLabel: '已驳回',
                rejectReason: '图片模糊，请重新上传'
            }
        ]
        this.setData({ certificates: mockData })
    },

    onItemClick(e) {
        const item = e.currentTarget.dataset.item
        if (item.status === 'rejected') {
            wx.navigateTo({
                url: `/pages/certificate_edit/certificate_edit?status=rejected&reason=${item.rejectReason || ''}&certName=${item.title}`,
            })
        }
    },

    onUpload() {
        wx.navigateTo({
            url: '/pages/certificate_edit/certificate_edit',
        })
    }
})
