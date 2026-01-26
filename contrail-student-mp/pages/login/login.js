Page({
  data: {
    idCardNo: '',
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

  onInputIdCardNo(e) {
    this.setData({
      idCardNo: e.detail.value
    });
  },

  onInputPassword(e) {
    this.setData({
      password: e.detail.value
    });
  },

  async onLogin() {
    const { idCardNo, password } = this.data;

    if (!idCardNo || !password) {
      wx.showToast({ title: '请输入身份证号和密码', icon: 'none' });
      return;
    }

    const { get, post } = require('../../utils/request');
    const { encryptWithPublicKey } = require('../../utils/rsa');

    wx.showLoading({ title: '登录中...' });

    try {
      // 1) 获取 RSA 公钥（后端要求密码必须加密）
      const pk = await get('/auth/public-key', null, { auth: false });
      const publicKeyPem = pk && (pk.public_key || pk.publicKey);
      if (!publicKeyPem) throw new Error('获取公钥失败');

      // 2) RSA 加密密码（PKCS#1 v1.5），得到 base64 字符串
      const encryptedPassword = encryptWithPublicKey(password, publicKeyPem);

      // 3) 登录
      const res = await post(
        '/auth/login',
        { id_card_no: String(idCardNo).trim(), password: encryptedPassword },
        { auth: false }
      );

      const token = res && (res.access_token || (res.data && res.data.token));
      const user = res && (res.user || (res.data && res.data.userInfo));
      if (!token) throw new Error('登录失败：未返回token');

      wx.setStorageSync('token', token);
      if (user) wx.setStorageSync('user', user);

      wx.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' });
      }, 800);
    } catch (e) {
      wx.showToast({ title: e.message || '登录失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  }
});
