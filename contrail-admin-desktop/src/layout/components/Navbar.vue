<template>
  <div class="navbar">
    <div class="left-menu">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
          {{ item.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="right-menu">
      <ThemeSwitch />
      <el-dropdown class="avatar-container" trigger="click">
        <div class="avatar-wrapper">
          <span class="user-name">{{ userStore.userInfo?.name || '用户' }}</span>
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ArrowDown } from '@element-plus/icons-vue'
import ThemeSwitch from '@/components/ThemeSwitch/index.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const breadcrumbs = computed(() => {
  return route.matched.filter(item => item.meta && item.meta.title && item.meta.title !== 'Dashboard')
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  // 玻璃拟态效果 - 浅色模式
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  color: var(--el-text-color-primary);
  transition: all 0.3s ease;

  .right-menu {
    display: flex;
    align-items: center;
    cursor: pointer;
    
    .avatar-wrapper {
      display: flex;
      align-items: center;
      color: var(--el-text-color-primary);
      transition: color 0.3s ease;
      
      .user-name {
        margin-right: 5px;
      }
    }
  }
}
</style>

<style lang="scss">
// 暗黑模式下的玻璃拟态效果
html.dark .navbar {
  background: rgba(0, 0, 0, 0.7);
  box-shadow: 0 1px 4px rgba(255, 255, 255, 0.05);
}
</style>
