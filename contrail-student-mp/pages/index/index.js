// index.js
Page({
    data: {
        paddingTop: 0,
        paddingBottom: 0,
        scrollViewHeight: 0,
        tabBarHeight: 0,
        loading: false,
        score: 85,
        statusList: [
            { name: '初试', status: 'qualified', label: '合格' },
            { name: '体检', status: 'pending', label: '待处理' },
            { name: '政审', status: 'unqualified', label: '不合格' },
            { name: '录取', status: 'pending', label: '待处理' }
        ],
        comment: '该生在校期间表现优秀，学习刻苦努力，成绩优异。积极参加各类社团活动，具有较强的团队协作能力和组织能力。思想品德良好，乐于助人，深受老师和同学喜爱。希望在未来的学习和工作中继续保持良好的作风，不断进取，取得更大的成绩。该生在校期间表现优秀，学习刻苦努力，成绩优异。积极参加各类社团活动，具有较强的团队协作能力和组织能力。'
    },
    onLoad() {
        // Calculate safe area
        const menuButtonInfo = wx.getMenuButtonBoundingClientRect();
        const windowInfo = wx.getWindowInfo();

        // Calculate paddingTop: Use safeArea.top (status bar height) + menu button height + spacing
        // For custom navigation, we need to account for status bar + menu button area
        const statusBarHeight = windowInfo.statusBarHeight || windowInfo.safeArea?.top || 0;
        const menuButtonHeight = menuButtonInfo.height || 32;
        // Calculate the space from status bar to menu button bottom
        const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonHeight;
        // Total top space needed: status bar + nav bar + extra spacing for content
        // This ensures content starts below the system UI
        const minTop = statusBarHeight + navBarHeight;
        const targetTop = windowInfo.windowHeight * 0.12; // 12% of screen height
        const paddingTop = Math.max(minTop, targetTop);

        // Calculate tabBar height (typically 48px + safe area bottom)
        const tabBarHeight = 48; // Standard tabBar height
        const safeAreaBottom = windowInfo.safeArea ? (windowInfo.screenHeight - windowInfo.safeArea.bottom) : 0;
        const totalTabBarHeight = tabBarHeight + safeAreaBottom;
        const paddingBottom = totalTabBarHeight + 20; // Add extra padding

        // Calculate scroll view height: windowHeight minus tabBar (scroll-view starts at top 0, container has paddingTop)
        // Note: scroll-view itself starts at (0,0), so we only need to account for tabBar at bottom
        const scrollViewHeight = windowInfo.windowHeight - totalTabBarHeight;

        this.setData({
            paddingTop,
            paddingBottom,
            scrollViewHeight,
            tabBarHeight: totalTabBarHeight
        });
    },
    onShow() {
        // tab 页每次切回都刷新一下数据
        this.fetchDashboard();
    },
    _statusLabel(status) {
        if (status === 'qualified') return '合格';
        if (status === 'unqualified') return '不合格';
        return '待处理';
    },
    _buildStatusList(processStatus) {
        const ps = processStatus || {};
        const list = [
            { key: 'preliminary', name: '初试' },
            { key: 'medical', name: '体检' },
            { key: 'political', name: '政审' },
            { key: 'admission', name: '录取' },
        ];
        return list.map((it) => {
            const status = ps[it.key] || 'pending';
            return { name: it.name, status, label: this._statusLabel(status) };
        });
    },
    async fetchDashboard() {
        if (this.data.loading) return;
        this.setData({ loading: true });

        const { get } = require('../../utils/request');
        try {
            // 1) 首选 dashboard（后端新增接口）
            const dashboard = await get('/student/dashboard');
            const score = (dashboard && (dashboard.score ?? dashboard.total_score)) ?? this.data.score;
            const comment = (dashboard && dashboard.comment) || '';
            const statusList = this._buildStatusList(dashboard && dashboard.process_status);

            this.setData({
                score,
                comment,
                statusList,
            });
        } catch (e) {
            // 2) 兜底：只拉积分，避免主页空白（比如后端未部署 dashboard）
            try {
                const scoreRes = await get('/student/score');
                const score = (scoreRes && (scoreRes.total_score ?? scoreRes.totalScore)) ?? this.data.score;
                if (score !== this.data.score) {
                    this.setData({ score });
                }
            } catch (_) {}

            wx.showToast({
                title: e.message || '主页数据加载失败',
                icon: 'none'
            });
        } finally {
            this.setData({ loading: false });
        }
    },
    onCommentTap() {
        if (!this.data.comment) {
            wx.showToast({ title: '暂无评语', icon: 'none' });
            return;
        }
        const q = encodeURIComponent(this.data.comment);
        wx.navigateTo({
            url: `/pages/comment/comment?comment=${q}`,
        });
    },
    onScoreTap() {
        wx.navigateTo({
            url: '/pages/score_detail/score_detail',
        });
    }
})
