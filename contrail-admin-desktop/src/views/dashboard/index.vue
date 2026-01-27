<template>
  <div class="dashboard-container">
    <h1>欢迎来到 Dashboard</h1>
    <el-button type="danger" @click="handleLogout">退出登录</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
</style>
