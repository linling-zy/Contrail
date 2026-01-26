const { get } = require('../../utils/request')

Page({
    data: {
        paddingTop: 0,
        scrollViewHeight: 0,
        certificates: [], // Certificate list
        isLoading: false,
    },

    onLoad() {
        this.initLayout()
        this.loadCertificates()
    },

    onPullDownRefresh() {
        this.loadCertificates().finally(() => {
            wx.stopPullDownRefresh()
        })
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

    /**
     * 将后端状态码映射为前端状态
     * 后端: 0=待审核, 1=通过, 2=驳回
     * 前端: 'auditing', 'passed', 'rejected'
     */
    mapStatus(status) {
        const map = {
            0: { status: 'auditing', label: '审核中' },
            1: { status: 'passed', label: '已通过' },
            2: { status: 'rejected', label: '已驳回' },
        }
        return map[status] || { status: 'auditing', label: '未知' }
    },

    async loadCertificates() {
        this.setData({ isLoading: true })
        try {
            const res = await get('/certificate/list')
            // 后端返回: { certificates: [...], warning?: '...' }
            const certs = (res.certificates || []).map(cert => {
                const statusInfo = this.mapStatus(cert.status)
                return {
                    id: cert.id,
                    title: cert.certName || cert.name || '未命名证书',
                    thumb: cert.imgUrl || '',
                    status: statusInfo.status,
                    statusLabel: statusInfo.label,
                    rejectReason: cert.reject_reason || '',
                }
            })
            this.setData({ certificates: certs })
            if (res.warning) {
                wx.showToast({ title: res.warning, icon: 'none', duration: 2000 })
            }
        } catch (err) {
            console.error('加载证书列表失败:', err)
            wx.showToast({
                title: err.message || '加载失败，请稍后重试',
                icon: 'none',
                duration: 2000,
            })
            this.setData({ certificates: [] })
        } finally {
            this.setData({ isLoading: false })
        }
    },

    onItemClick(e) {
        const item = e.currentTarget.dataset.item
        if (item.status === 'rejected') {
            wx.navigateTo({
                url: `/pages/certificate_edit/certificate_edit?status=rejected&reason=${encodeURIComponent(item.rejectReason || '')}&certName=${encodeURIComponent(item.title)}&certId=${item.id}`,
            })
        }
    },

    onUpload() {
        wx.navigateTo({
            url: '/pages/certificate_edit/certificate_edit',
        })
    }
})
