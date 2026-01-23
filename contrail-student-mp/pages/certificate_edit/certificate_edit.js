Page({
    data: {
        isRejected: false,
        rejectReason: '',
        selectedCert: '',
        imagePath: '',
        showPicker: false,
        searchText: '',
        certList: [
            '英语四级证书 (CET-4)',
            '英语六级证书 (CET-6)',
            '计算机二级证书 (NCRE-2)',
            '计算机三级证书 (NCRE-3)',
            '普通话一级乙等',
            '普通话二级甲等',
            '教师资格证',
            '初级会计职称',
            '中级会计职称',
            '法律职业资格证书'
        ],
        filteredList: [],
        navBarHeight: 0,
        statusBarHeight: 0,
        headerHeight: 0
    },

    onLoad(options) {
        this.initLayout()

        if (options.status === 'rejected') {
            this.setData({
                isRejected: true,
                rejectReason: options.reason || '图片质量不符合要求'
            })
            // If editing existing item, you might preload data here
            if (options.certName) {
                this.setData({ selectedCert: options.certName })
            }
        }

        // Initialize filtered list
        this.setData({ filteredList: this.data.certList })
    },

    initLayout() {
        const menuButtonInfo = wx.getMenuButtonBoundingClientRect()
        const windowInfo = wx.getWindowInfo()

        const statusBarHeight = windowInfo.statusBarHeight || windowInfo.safeArea?.top || 0
        const menuButtonHeight = menuButtonInfo.height || 32
        const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonHeight
        const headerHeight = statusBarHeight + navBarHeight

        this.setData({
            statusBarHeight,
            navBarHeight,
            headerHeight
        })
    },

    onBack() {
        wx.navigateBack()
    },

    // Picker Logic
    togglePicker() {
        if (this.data.isRejected) {
            return; // Disable picker in rejected mode
        }
        this.setData({
            showPicker: !this.data.showPicker,
            searchText: '',
            filteredList: this.data.certList // Reset search on open
        })
    },

    stopProp() {
        // Prevent closing when clicking content
    },

    onSearch(e) {
        const text = e.detail.value
        const filtered = this.data.certList.filter(item =>
            item.toLowerCase().includes(text.toLowerCase())
        )
        this.setData({
            searchText: text,
            filteredList: filtered
        })
    },

    onSelectCert(e) {
        const name = e.currentTarget.dataset.name
        this.setData({
            selectedCert: name,
            showPicker: false
        })
    },

    // Upload Logic
    onUpload() {
        wx.chooseMedia({
            count: 1,
            mediaType: ['image'],
            sourceType: ['album', 'camera'],
            success: (res) => {
                const tempPath = res.tempFiles[0].tempFilePath
                this.setData({ imagePath: tempPath })
            }
        })
    },

    onRemoveImg() {
        this.setData({ imagePath: '' })
    },

    previewImage() {
        if (this.data.imagePath) {
            wx.previewImage({
                urls: [this.data.imagePath],
            })
        }
    },

    // Submit Logic
    onSubmit() {
        const { selectedCert, imagePath } = this.data

        if (!selectedCert) {
            wx.showToast({ title: '请选择证书名称', icon: 'none' })
            return
        }

        if (!imagePath) {
            wx.showToast({ title: '请上传证书凭证', icon: 'none' })
            return
        }

        wx.showLoading({ title: '提交中...' })

        // Simulate Network Request
        setTimeout(() => {
            wx.hideLoading()
            wx.showToast({
                title: '提交成功',
                icon: 'success',
                duration: 2000,
                success: () => {
                    setTimeout(() => {
                        wx.navigateBack()
                    }, 1500)
                }
            })
        }, 1500)
    }
})
