// score_detail.js
Page({
    data: {
        paddingTop: 0,
        paddingBottom: 0,
        scrollViewHeight: 0,
        loading: false,
        baseScore: 0,
        totalScore: 0,
        scoreLogs: []
    },
    onLoad() {
        // Calculate navigation bar height
        const windowInfo = wx.getWindowInfo();
        const platform = (wx.getDeviceInfo() || wx.getSystemInfoSync()).platform;
        const isAndroid = platform === 'android';
        
        // 导航栏组件高度：iOS 44px, Android 48px，加上状态栏高度
        const statusBarHeight = windowInfo.statusBarHeight || windowInfo.safeArea?.top || 0;
        const navBarContentHeight = isAndroid ? 48 : 44;
        // 导航栏总高度 = 状态栏 + 导航栏内容
        const navBarTotalHeight = statusBarHeight + navBarContentHeight;
        // 使用导航栏总高度，让内容紧贴导航栏底部
        const paddingTop = navBarTotalHeight;

        const paddingBottom = 20;
        const scrollViewHeight = windowInfo.windowHeight;

        this.setData({
            paddingTop,
            paddingBottom,
            scrollViewHeight
        });

        this.fetchScoreDetail();
    },
    async fetchScoreDetail() {
        if (this.data.loading) return;
        this.setData({ loading: true });

        const { get } = require('../../utils/request');
        try {
            const res = await get('/student/score');
            this.setData({
                baseScore: res.base_score || 0,
                totalScore: res.total_score || 0,
                scoreLogs: res.score_logs || []
            });
        } catch (e) {
            wx.showToast({
                title: e.message || '分数明细加载失败',
                icon: 'none'
            });
        } finally {
            this.setData({ loading: false });
        }
    },
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    }
})

