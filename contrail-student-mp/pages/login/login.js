Page({
  data: {
    username: '',
    password: '',
    statusBarHeight: 20,
    navBarHeight: 44,
    menuButtonHeight: 32,
    menuButtonTop: 26
  },

  onLoad() {
    const windowInfo = wx.getWindowInfo();
    const menuButtonInfo = wx.getMenuButtonBoundingClientRect();

    this.setData({
      statusBarHeight: windowInfo.statusBarHeight,
      navBarHeight: (menuButtonInfo.top - windowInfo.statusBarHeight) * 2 + menuButtonInfo.height,
      menuButtonHeight: menuButtonInfo.height,
      menuButtonTop: menuButtonInfo.top
    });
  },

  onInputUsername(e) {
    this.setData({
      username: e.detail.value
    });
  },

  onInputPassword(e) {
    this.setData({
      password: e.detail.value
    });
  },

  onLogin() {
    const { username, password } = this.data;

    if (!username || !password) {
      wx.showToast({
        title: '请输入账号和密码',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '登录中...',
    });

    // Simulate API call
    setTimeout(() => {
      wx.hideLoading();

      // Fake login logic: Accept any non-empty input for now, 
      // or we could enforce specific credentials like 'admin/123456'.
      // For this task, we'll accept 'student' as a valid user testing scenario.
      if (username) {
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        });

        // Navigate to home page after short delay
        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }, 1500);
      } else {
        wx.showToast({
          title: '用户名或密码错误',
          icon: 'none'
        });
      }
    }, 1000);
  }
});
