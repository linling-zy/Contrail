const { uploadFile, get } = require('../../utils/request')

Page({
    data: {
        isRejected: false,
        rejectReason: '',
        selectedCert: '',
        imagePath: '',
        showPicker: false,
        searchText: '',
        certId: null,
        certList: [],
        filteredList: [],
        navBarHeight: 0,
        statusBarHeight: 0,
        headerHeight: 0,
        isSubmitting: false,
        isLoadingCertTypes: false,
        hasNoCertTypes: false,

        // Dynamic Form Data
        formType: '', // 'CET', 'IELTS', 'JOB', 'AWARD', 'DEFAULT'
        isNameEditable: false, // For JOB and AWARD
        awardLevels: ['国家级', '省部级', '校级', '院级'],
        awardLevelIndex: -1, // For Picker

        // Field Values
        // Field Values
        formData: {
            score: '', // CET Score
            ielts_listening: '',
            ielts_reading: '',
            ielts_writing: '',
            ielts_speaking: '',
            ielts_total: '',
            job_start_date: '', // JOB Start
            job_end_date: '',   // JOB End
            job_title: '',
            job_award: '', // 集体获奖情况
            award_date: '',
            award_name: '', // 奖励名称
            award_org: '', // 主办单位
            award_level: '', // 奖励级别
            award_rank: '', // 获奖等次
            user_defined_name: '', // User editable cert name
        }
    },

    onLoad(options) {
        this.initLayout()
        this.loadCertificateTypes()

        // Handle Type passed from Grid
        if (options.type) {
            let type = options.type
            const name = decodeURIComponent(options.certName || '')

            // Normalize CET4/CET6 to CET for form display
            if (type === 'CET4' || type === 'CET6') {
                type = 'CET'
            }

            this.setData({
                selectedCert: name,
                formType: type,
                // Only allow name editing if it's JOB or AWARD
                isNameEditable: (type === 'JOB' || type === 'AWARD'),
            })

            // Initialize form data based on type
            this.initFormData(type, name)
        }
        // Handle Rejected Status
        else if (options.status === 'rejected') {
            this.setData({
                isRejected: true,
                rejectReason: decodeURIComponent(options.reason || '图片质量不符合要求'),
            })
            if (options.certName) {
                const name = decodeURIComponent(options.certName)
                this.setData({ selectedCert: name })
                this.detectFormType(name)
            }
            if (options.certId) {
                this.setData({ certId: parseInt(options.certId, 10) })
            }
        }
    },

    initFormData(type, name) {
        const initialData = {
            score: '',
            ielts_listening: '',
            ielts_reading: '',
            ielts_writing: '',
            ielts_speaking: '',
            ielts_total: '',
            job_start_date: '',
            job_end_date: '',
            job_title: '',
            job_award: '',
            award_date: '',
            award_name: '',
            award_org: '',
            award_level: '',
            award_rank: '',
            user_defined_name: (type === 'JOB' || type === 'AWARD') ? name : '',
        }

        this.setData({
            formData: initialData,
            awardLevelIndex: -1
        })
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

    async loadCertificateTypes() {
        this.setData({ isLoadingCertTypes: true })
        try {
            const res = await get('/certificate/types')
            const certTypes = res.certificate_types || []
            const certNames = certTypes.map(item => item.name).filter(Boolean)

            if (certNames.length > 0) {
                this.setData({
                    certList: certNames,
                    filteredList: certNames,
                    hasNoCertTypes: false,
                })
            } else {
                this.setData({
                    certList: [],
                    filteredList: [],
                    hasNoCertTypes: true,
                })
            }
        } catch (err) {
            console.error('加载证书类型列表失败:', err)
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
            return;
        }
        // If formType is set (from Grid), prevent changing type unless it's a re-selection logic we want to support?
        // Plan said: "Disable picker if type is passed via URL."
        // We can check if options.type was present, but let's just use existing formType check if we want to lock it.
        // Actually, for "Job"/"Award", we want them to re-select? No, they selected "Job" entry.
        // So we should probably hide the picker trigger or disable it.
        // For now, let's allow it ONLY if it wasn't pre-set or if we want flexibility.
        // But per request "Specific entrance", it implies fixed type.
        if (this.data.formType && this.data.formType !== 'DEFAULT' && !this.data.isNameEditable) {
            return;
        }

        if (this.data.isLoadingCertTypes) {
            wx.showToast({ title: '证书列表加载中，请稍候', icon: 'none' })
            return
        }
        this.setData({
            showPicker: !this.data.showPicker,
            searchText: '',
            filteredList: this.data.certList
        })
    },

    stopProp() { },

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
        this.detectFormType(name)
    },

    // Form Type Logic
    detectFormType(name) {
        let type = 'DEFAULT'
        let isNameEditable = false

        // Enhanced detection for CET certificates
        if (name.includes('英语四级') || name.includes('英语六级') ||
            name.includes('CET') || name.includes('四级') || name.includes('六级') ||
            name.includes('大学英语四级') || name.includes('大学英语六级')) {
            type = 'CET'
        } else if (name.includes('雅思') || name.includes('IELTS')) {
            type = 'IELTS'
        } else if (name.includes('任职')) {
            type = 'JOB'
            isNameEditable = true
        } else if (name.includes('获奖')) {
            type = 'AWARD'
            isNameEditable = true
        }

        // Reset formData when type changes
        const initialData = {
            score: '',
            ielts_listening: '',
            ielts_reading: '',
            ielts_writing: '',
            ielts_speaking: '',
            ielts_total: '',
            job_start_date: '',
            job_end_date: '',
            job_title: '',
            job_award: '',
            award_date: '',
            award_name: '',
            award_org: '',
            award_level: '',
            award_rank: '',
            user_defined_name: isNameEditable ? name : '',
        }

        this.setData({
            formType: type,
            isNameEditable: isNameEditable,
            formData: initialData,
            awardLevelIndex: -1
        })
    },

    // Input Handlers
    onInputChange(e) {
        const field = e.currentTarget.dataset.field
        const value = e.detail.value
        this.setData({
            [`formData.${field}`]: value
        })
    },

    onDateChange(e) {
        const field = e.currentTarget.dataset.field
        const value = e.detail.value
        this.setData({
            [`formData.${field}`]: value
        })
    },

    onLevelChange(e) {
        const index = e.detail.value
        this.setData({
            awardLevelIndex: index,
            'formData.award_level': this.data.awardLevels[index]
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
        const { selectedCert, imagePath, isSubmitting, formType, formData, isNameEditable } = this.data

        if (isSubmitting) return

        if (!selectedCert) {
            wx.showToast({ title: '请选择证书类型', icon: 'none' })
            return
        }

        // Validate Dynamic Fields
        let extraData = {}
        const finalCertName = isNameEditable && formData.user_defined_name ? formData.user_defined_name : selectedCert

        if (formType === 'CET') {
            if (!formData.score) return this.warn('请输入考试分数')
            extraData = { score: formData.score }
        } else if (formType === 'IELTS') {
            if (!formData.ielts_total) return this.warn('请输入雅思总分')
            if (!formData.ielts_listening) return this.warn('请输入听力分数')
            if (!formData.ielts_reading) return this.warn('请输入阅读分数')
            if (!formData.ielts_writing) return this.warn('请输入写作分数')
            if (!formData.ielts_speaking) return this.warn('请输入口语分数')

            extraData = {
                listening: formData.ielts_listening,
                reading: formData.ielts_reading,
                writing: formData.ielts_writing,
                speaking: formData.ielts_speaking,
                total: formData.ielts_total
            }
        } else if (formType === 'JOB') {
            if (!formData.job_start_date || !formData.job_end_date) return this.warn('请完整选择任职起止时间')
            if (formData.job_start_date > formData.job_end_date) return this.warn('开始时间不能晚于结束时间')
            if (!formData.job_title) return this.warn('请输入担任职务')

            // Format date range: YYYY-MM至YYYY-MM
            // Assume picker value is YYYY-MM-DD or similar, we might want to trim to YYYY-MM or keep as is?
            // Requirment says: "YYYY-MM 至 YYYY-MM"
            const start = formData.job_start_date.slice(0, 7) // 2023-01
            const end = formData.job_end_date.slice(0, 7)
            const dateRange = `${start} 至 ${end}`

            extraData = {
                date: dateRange,
                position: formData.job_title,
                award: formData.job_award || '无'
            }
        } else if (formType === 'AWARD') {
            if (!formData.award_date) return this.warn('请选择获奖时间')
            if (!formData.award_name) return this.warn('请输入奖励名称')
            if (!formData.award_org) return this.warn('请输入主办单位')
            if (!formData.award_level) return this.warn('请选择奖励级别')
            if (!formData.award_rank) return this.warn('请输入获奖等次')
            extraData = {
                date: formData.award_date,
                name: formData.award_name,
                organizer: formData.award_org,
                level: formData.award_level,
                rank: formData.award_rank
            }
        }

        if (!imagePath) {
            return this.warn('请上传证书凭证')
        }

        this.setData({ isSubmitting: true })
        wx.showLoading({ title: '上传中...', mask: true })

        try {
            // Include certId if it's a resubmission (rejected)
            // But API usually just uses POST /upload for new. 
            // If editing, maybe different endpoint? 
            // Assuming this is just "re-upload" as a new item or same item logic handled by backend if we don't pass ID?
            // Prompt says "extraData" field.

            const postData = {
                certName: finalCertName,
                extraData: JSON.stringify(extraData)
            }
            if (this.data.certId) {
                postData.certId = this.data.certId // Pass ID if re-uploading, backend might need it
            }

            await uploadFile({
                url: '/certificate/upload',
                filePath: imagePath,
                name: 'file',
                formData: postData,
            })

            wx.hideLoading()
            wx.showToast({
                title: '提交成功',
                icon: 'success',
                duration: 2000,
                success: () => {
                    setTimeout(() => {
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

    warn(msg) {
        wx.showToast({ title: msg, icon: 'none' })
        return false // indicate failure
    }
})
