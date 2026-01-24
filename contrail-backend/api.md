

### 一、 核心 API 接口定义 (RESTful 风格建议)

建议统一 BaseURL，例如：`https://api.contrail.com/api/v1`

#### 1. 用户与认证 (对应 `pages/login`)

你目前的 `login.js` 使用了账号密码登录。

* **接口地址**: `POST /auth/login`
* **请求参数**:
```json
{
  "username": "student_id_or_name",
  "password": "raw_password" 
}

```


* **响应数据**:
```json
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1...", // 核心：JWT Token，后续请求都要带上
    "userInfo": { "name": "张三", "role": "student" }
  }
}

```


* **前端逻辑**: 拿到 `token` 后，必须使用 `wx.setStorageSync('token', res.data.token)` 存入本地。

#### 2. 首页仪表盘 (对应 `pages/index`)

首页的数据比较杂（分数、四个阶段的状态、评语），建议合并为一个接口请求，减少白屏等待。

* **接口地址**: `GET /student/dashboard`
* **请求头**: `Authorization: Bearer <token>`
* **响应数据** (对应你 `index.js` 中的 `data`):
```json
{
  "code": 200,
  "data": {
    "score": 85,
    "comment": "该生在校期间表现优秀...",
    // 对应你的 statusList，建议后端直接返回状态码，前端映射颜色和图标
    "process_status": {
        "preliminary": "qualified", // 初试
        "medical": "qualified",     // 体检
        "political": "unqualified", // 政审
        "admission": "pending"      // 录取
    }
  }
}

```



#### 3. 个人信息 (对应 `pages/my`)

* **接口地址**: `GET /student/profile`
* **响应数据** (对应 `my.js` 中的 `userInfo`):
```json
{
  "name": "张三",
  "studentId": "2023001",
  "college": "计算机学院",
  "major": "软件工程",
  "grade": "2023级",
  "class_name": "2301班"
}

```



#### 4. 证书模块 (核心交互难点)

这里涉及**列表展示**和**文件上传**两部分。

**A. 获取证书列表 (对应 `pages/certificates`)**

* **接口地址**: `GET /certificates`
* **响应数据**:
```json
[
  {
    "id": 101,
    "title": "英语六级",
    "status": 1, // 1: 通过, 0: 审核中, -1: 驳回
    "status_label": "已通过", // 可选，也可以前端转义
    "thumb_url": "https://oss.xxx.com/img/cert_001.jpg",
    "reject_reason": null
  }
]

```



**B. 图片上传 (对应 `certificate_edit.js` 的 `onUpload`)**
小程序上传文件不能用普通的 JSON POST，必须用 `wx.uploadFile`。

* **接口地址**: `POST /common/upload`
* **Content-Type**: `multipart/form-data`
* **响应数据**:
```json
{
  "url": "https://oss.yourdomain.com/uploads/2026/01/xxx.jpg", // 必须返回图片的远程地址
  "file_id": "12345" // 可选
}

```



**C. 提交/修改证书 (对应 `certificate_edit.js` 的 `onSubmit`)**
拿到图片 URL 后，再提交表单。

* **接口地址**: `POST /certificates` (如果是修改则是 `PUT /certificates/{id}`)
* **请求参数**:
```json
{
  "title": "计算机二级", // 证书名称
  "image_url": "https://oss.../xxx.jpg" // 上一步拿到的图片地址
}

```



---

### 二、 需要注意的技术细节 (Technical Details)

#### 1. 网络请求封装 (Request Wrapper)

你现在的代码里大量使用了 `setTimeout` 模拟。在对接时，千万不要在每个页面直接写 `wx.request`。
**建议创建一个 `utils/request.js` 文件：**

* **统一注入 Token**: 每次请求自动从 `wx.getStorageSync` 读取 Token 放入 Header。
* **统一处理 BaseURL**: 开发环境和生产环境切换。
* **统一处理 401 错误**: 如果 Token 过期（后端返回 401），自动跳转回 `pages/login`。

#### 2. 证书上传的“坑”

在 `pages/certificate_edit/certificate_edit.js` 中：

* **当前逻辑**: `onUpload` 只是把 `tempFilePath` (临时路径) 存到了 `data` 里。
* **修改建议**: 在点击“提交”按钮时，流程应该是：
1. 判断 `imagePath` 是本地临时路径（`wxfile://` 开头）还是网络路径（`http` 开头）。
2. 如果是本地路径 -> **先调用上传 API** -> 拿到 URL。
3. 如果是网络路径（比如编辑已有证书并未修改图片） -> 跳过上传。
4. 最后调用 **提交证书 API**。



#### 3. 状态枚举管理

在 `index.js` 和 `certificates.js` 中，你使用了字符串来判断状态（如 `'qualified'`, `'passed'`）。
**建议**: 前后端约定好**状态码 (Int)**，例如：

* `0`: Pending (待审核/待处理)
* `1`: Qualified/Passed (合格/通过)
* `2`: Rejected/Unqualified (不合格/驳回)
这样后端改状态文案（比如把“不合格”改为“未通过”），前端不需要改代码。

### 三、 下一步建议

既然你已经有了 `contrail-backend` 文件夹（虽然目前只有 `api.md`），我建议你下一步：

1. **完善 `api.md**`: 把我上面提到的接口格式复制进去，作为前后端开发的契约。
2. **封装 Request**: 我可以帮你写一个适配你当前代码风格的 `request.js` 封装函数，你需要吗？
3. **Mock 对接**: 如果后端还没好，可以使用 Apifox 或 Postman Mock Server 按照上述文档生成 Mock 地址，先让小程序跑通网络流程。

你想先处理哪一部分？是**网络请求的封装代码**，还是**证书上传的具体逻辑实现**？