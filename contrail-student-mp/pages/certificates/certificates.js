const { get } = require('../../utils/request')

Page({
    data: {
        paddingTop: 0,
        scrollViewHeight: 0,
        certificates: [], // Displayed list
        allCertificates: [], // Full list
        isLoading: false,
        activeFilter: 'all', // all, auditing, passed, rejected
        entryList: [
            {
                type: 'CET4',
                name: '英语四级',
                watermark: 'CET4',
                styleClass: 'card-small',
                gradient: 'linear-gradient(135deg, #E0C3FC 0%, #8EC5FC 100%)',
                shadow: 'rgba(142, 197, 252, 0.3)'
            },
            {
                type: 'CET6',
                name: '英语六级',
                watermark: 'CET6',
                styleClass: 'card-small',
                gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
                shadow: 'rgba(161, 140, 209, 0.3)'
            },
            {
                type: 'IELTS',
                name: '雅思 IELTS',
                watermark: 'IELTS',
                styleClass: 'card-small',
                gradient: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',
                shadow: 'rgba(161, 196, 253, 0.3)'
            },
            {
                type: 'JOB',
                name: '任职经历',
                watermark: 'Experience',
                styleClass: 'card-medium',
                gradient: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
                shadow: 'rgba(132, 250, 176, 0.3)'
            },
            {
                type: 'AWARD',
                name: '获奖情况',
                watermark: 'Award',
                styleClass: 'card-medium',
                gradient: 'linear-gradient(120deg, #f6d365 0%, #fda085 100%)',
                shadow: 'rgba(246, 211, 101, 0.3)'
            }
        ]
    },

    onLoad() {
        this.initLayout()
        this.loadCertificates()
    },

    onShow() {
        // Reload list when returning (e.g. after adding)
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
        const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonHeight
        const totalTop = statusBarHeight + navBarHeight

        const safeAreaBottom = windowInfo.safeArea ? (windowInfo.screenHeight - windowInfo.safeArea.bottom) : 0
        const tabBarHeight = 48 + safeAreaBottom

        const scrollViewHeight = windowInfo.windowHeight - tabBarHeight

        this.setData({
            paddingTop: totalTop,
            scrollViewHeight: scrollViewHeight,
            navBarHeight: navBarHeight,
            statusBarHeight: statusBarHeight
        })
    },

    /**
     * Map backend status to frontend status
     * Backend: 0=auditing, 1=passed, 2=rejected
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
            const certs = (res.certificates || []).map(cert => {
                const statusInfo = this.mapStatus(cert.status)
                return {
                    id: cert.id,
                    title: cert.certName || cert.name || '未命名证书',
                    thumb: cert.imgUrl || '',
                    status: statusInfo.status,
                    statusLabel: statusInfo.label,
                    rejectReason: cert.reject_reason || '',
                    date: cert.createTime ? cert.createTime.split(' ')[0] : '', // Simple date format
                    type: cert.type || 'CERT' // Assuming type field exists
                }
            })

            this.setData({
                allCertificates: certs
            }, () => {
                this.filterCertificates()
            })

            if (res.warning) {
                wx.showToast({ title: res.warning, icon: 'none', duration: 2000 })
            }
        } catch (err) {
            console.error('Failed to load certificates:', err)
            wx.showToast({
                title: err.message || '加载失败',
                icon: 'none',
                duration: 2000,
            })
            this.setData({ allCertificates: [], certificates: [] })
        } finally {
            this.setData({ isLoading: false })
        }
    },

    onFilterClick(e) {
        const type = e.currentTarget.dataset.type
        if (type === this.data.activeFilter) return

        this.setData({ activeFilter: type }, () => {
            this.filterCertificates()
        })
    },

    filterCertificates() {
        const { allCertificates, activeFilter } = this.data
        if (activeFilter === 'all') {
            this.setData({ certificates: allCertificates })
        } else {
            const filtered = allCertificates.filter(item => item.status === activeFilter)
            this.setData({ certificates: filtered })
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

    onEntryTap(e) {
        const item = e.currentTarget.dataset.item
        if (!item) return

        wx.navigateTo({
            url: `/pages/certificate_edit/certificate_edit?type=${item.type}&certName=${encodeURIComponent(item.name)}`
        })
    }
})
