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
        path: '/setup',
        name: 'Setup',
        component: () => import('@/views/setup/index.vue'),
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
                path: 'department/:id',
                name: 'DepartmentDetail',
                component: () => import('@/views/system/department-detail.vue'),
                meta: { title: '部门详情', activeMenu: '/system/department' },
                hidden: true
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

import { getSystemInitStatus } from '@/api/system'

let hasCheckedInit = false
let isInitialized = true // 默认假设已初始化，避免阻塞，等待 api 确认

router.beforeEach(async (to, from, next) => {
    // 1. 系统初始化检查 (最高优先级)
    if (!hasCheckedInit) {
        try {
            const res = await getSystemInitStatus()
            // 后端返回 { initialized: boolean }
            // 注意：需根据实际返回结构调整，假设直接返回对象
            isInitialized = res.initialized !== false // 如果明确为 false 才算未初始化
            hasCheckedInit = true
        } catch (error) {
            console.error('Failed to check system status:', error)
            // 请求失败时，假设系统未初始化，允许访问 setup 页面
            // 这样即使后端未启动或 CORS 问题，用户仍可以访问初始化页面
            isInitialized = false
            hasCheckedInit = true
        }
    }

    if (!isInitialized) {
        if (to.path === '/setup') {
            next()
        } else {
            next('/setup')
        }
        return
    } else {
        // 已初始化
        if (to.path === '/setup') {
            next('/login')
            return
        }
    }

    // 2. 原有的 Token 校验逻辑
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
            // 检查路由权限（包括父路由的权限）
            const checkRouteRoles = (route) => {
                // 检查当前路由的权限
                if (route.meta && route.meta.roles) {
                    return route.meta.roles
                }
                // 检查父路由的权限（递归查找）
                if (route.matched && route.matched.length > 1) {
                    for (let i = route.matched.length - 1; i >= 0; i--) {
                        const matchedRoute = route.matched[i]
                        if (matchedRoute.meta && matchedRoute.meta.roles) {
                            return matchedRoute.meta.roles
                        }
                    }
                }
                return null
            }
            
            const requiredRoles = checkRouteRoles(to)
            
            if (requiredRoles) {
                const hasRole = userStore.userInfo && requiredRoles.includes(userStore.userInfo.role)
                if (hasRole) {
                    next()
                } else {
                    try {
                        // 如果用户信息尚未加载（刷新页面情况），可能需要重新获取（此处简化依赖localStorage/store状态）
                        if (userStore.userInfo) {
                            // 用户有信息但没有权限，跳转到仪表盘
                            next({ path: '/dashboard' })
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
