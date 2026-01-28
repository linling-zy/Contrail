import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import Layout from '@/layout/index.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/login/index.vue'),
        hidden: true
    },
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/dashboard/index.vue'),
                meta: { title: '仪表盘', icon: 'Odometer' }
            }
        ]
    },
    {
        path: '/certificates',
        component: Layout,
        children: [
            {
                path: '',
                name: 'Certificates',
                component: () => import('@/views/certificates/index.vue'),
                meta: { title: '证书审核', icon: 'Document' }
            }
        ]
    },
    {
        path: '/students',
        component: Layout,

        children: [
            {
                path: '',
                name: 'DepartmentCards',
                component: () => import('@/views/students/DepartmentCards.vue'),
                meta: { title: '学生管理', icon: 'User' }
            },
            {
                path: 'class/:classId',
                name: 'ClassList',
                component: () => import('@/views/students/ClassList.vue'),
                meta: { title: '班级学生', activeMenu: '/students' },
                hidden: true
            },
            {
                path: 'status/:id',
                name: 'StudentStatusEdit',
                component: () => import('@/views/students/StatusEdit.vue'),
                meta: { title: '状态档案管理', activeMenu: '/students' },
                hidden: true
            }
        ]
    },
    {
        path: '/system',
        component: Layout,
        meta: { title: '系统设置', icon: 'Setting', roles: ['super'] },
        redirect: '/system/department',
        children: [
            {
                path: 'department',
                name: 'Department',
                component: () => import('@/views/system/department.vue'),
                meta: { title: '部门管理' }
            },
            {
                path: 'cert-type',
                name: 'CertType',
                component: () => import('@/views/system/cert-type.vue'),
                meta: { title: '证书类型' }
            },
            {
                path: 'admin',
                name: 'Admin',
                component: () => import('@/views/system/admin.vue'),
                meta: { title: '管理员管理' }
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const userStore = useUserStore()
    const token = userStore.token

    if (to.path === '/login') {
        if (token) {
            next({ path: '/' })
        } else {
            next()
        }
    } else {
        if (token) {
            // 简单的角色检查
            // 实际项目中应在获取用户信息后再生成路由，这里做简单拦截
            if (to.meta.roles) {
                const hasRole = userStore.userInfo && to.meta.roles.includes(userStore.userInfo.role)
                if (hasRole) {
                    next()
                } else {
                    try {
                        // 如果用户信息尚未加载（刷新页面情况），可能需要重新获取（此处简化依赖localStorage/store状态）
                        if (userStore.userInfo) {
                            next({ path: '/404' }) // 或者其他无权限页面
                        } else {
                            // 尝试恢复用户信息或跳转登录
                            userStore.logout()
                            next('/login')
                        }
                    } catch (e) {
                        next('/login')
                    }
                }
            } else {
                next()
            }
        } else {
            next('/login')
        }
    }
})

export default router
