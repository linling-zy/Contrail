const { uploadFile, get } = require('../../utils/request')

Page({
    data: {
        isRejected: false,
        rejectReason: '',
        selectedCert: '',
        imagePath: '',
        showPicker: false,
        searchText: '',
        certId: null, // 如果是重新上传被驳回的证书，记录原证书ID
        certList: [], // 从后端API获取
        filteredList: [],
        navBarHeight: 0,
        statusBarHeight: 0,
        headerHeight: 0,
        isSubmitting: false,
        isLoadingCertTypes: false, // 证书类型列表加载状态
        hasNoCertTypes: false, // 是否没有证书类型需要提交
    },

    onLoad(options) {
        this.initLayout()
        this.loadCertificateTypes() // 加载证书类型列表

        if (options.status === 'rejected') {
            this.setData({
                isRejected: true,
                rejectReason: decodeURIComponent(options.reason || '图片质量不符合要求'),
            })
            if (options.certName) {
                this.setData({ selectedCert: decodeURIComponent(options.certName) })
            }
            if (options.certId) {
                this.setData({ certId: parseInt(options.certId, 10) })
            }
        }
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

    /**
     * 从后端API加载证书类型列表
     * 接口: GET /api/certificate/types
     * 返回: { certificate_types: [{ id, name, description, is_required, ... }] }
     */
    async loadCertificateTypes() {
        this.setData({ isLoadingCertTypes: true })
        try {
            const res = await get('/certificate/types')
            // 提取证书名称列表
            const certTypes = res.certificate_types || []
            const certNames = certTypes.map(item => item.name).filter(Boolean)
            
            if (certNames.length > 0) {
                this.setData({
                    certList: certNames,
                    filteredList: certNames,
                    hasNoCertTypes: false,
                })
            } else {
                // 没有证书类型需要提交
                this.setData({
                    certList: [],
                    filteredList: [],
                    hasNoCertTypes: true,
                })
            }
        } catch (err) {
            console.error('加载证书类型列表失败:', err)
            // API调用失败时也显示空状态
            this.setData({
                certList: [],
                filteredList: [],
                hasNoCertTypes: true,
            })
        } finally {
            this.setData({ isLoadingCertTypes: false })
        }
    },

    onBack() {
        wx.navigateBack()
    },

    // Picker Logic
    togglePicker() {
        if (this.data.isRejected) {
            return; // Disable picker in rejected mode
        }
        if (this.data.isLoadingCertTypes) {
            wx.showToast({ title: '证书列表加载中，请稍候', icon: 'none' })
            return
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
    async onSubmit() {
        const { selectedCert, imagePath, isSubmitting } = this.data

        if (isSubmitting) return

        if (!selectedCert) {
            wx.showToast({ title: '请选择证书名称', icon: 'none' })
            return
        }

        if (!imagePath) {
            wx.showToast({ title: '请上传证书凭证', icon: 'none' })
            return
        }

        this.setData({ isSubmitting: true })
        wx.showLoading({ title: '上传中...', mask: true })

        try {
            // 使用 uploadFile 上传证书
            // 后端要求: file (文件), certName (证书名称)
            await uploadFile({
                url: '/certificate/upload',
                filePath: imagePath,
                name: 'file', // 后端期望的字段名
                formData: {
                    certName: selectedCert,
                },
            })

            wx.hideLoading()
            wx.showToast({
                title: '提交成功',
                icon: 'success',
                duration: 2000,
                success: () => {
                    setTimeout(() => {
                        // 返回上一页并触发刷新（通过事件或直接刷新）
                        const pages = getCurrentPages()
                        const prevPage = pages[pages.length - 2]
                        if (prevPage && typeof prevPage.loadCertificates === 'function') {
                            prevPage.loadCertificates()
                        }
                        wx.navigateBack()
                    }, 1500)
                },
            })
        } catch (err) {
            wx.hideLoading()
            console.error('证书上传失败:', err)
            wx.showToast({
                title: err.message || '上传失败，请稍后重试',
                icon: 'none',
                duration: 3000,
            })
        } finally {
            this.setData({ isSubmitting: false })
        }
    },
})
