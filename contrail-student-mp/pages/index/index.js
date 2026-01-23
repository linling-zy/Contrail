// index.js
Page({
    data: {
        paddingTop: 0,
        paddingBottom: 0,
        scrollViewHeight: 0,
        tabBarHeight: 0,
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
    onCommentTap() {
        wx.navigateTo({
            url: '/pages/comment/comment',
        });
    }
})
