<template>
  <el-scrollbar wrap-class="scrollbar-wrapper">
    <el-menu
      :default-active="activeMenu"
      :background-color="variables.menuBg"
      :text-color="variables.menuText"
      :active-text-color="variables.menuActiveText"
      :collapse-transition="false"
      mode="vertical"
      router
    >
      <div class="logo-container">
        <h3>航迹云</h3>
      </div>
      
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>

      <el-menu-item index="/certificates">
        <el-icon><Document /></el-icon>
        <span>证书审核</span>
      </el-menu-item>

      <el-menu-item index="/students">
        <el-icon><User /></el-icon>
        <span>学生管理</span>
      </el-menu-item>

      <el-sub-menu v-if="userStore.userInfo?.role === 'super'" index="/system">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </template>
        <el-menu-item index="/system/department">部门管理</el-menu-item>
        <el-menu-item index="/system/cert-type">证书类型</el-menu-item>
        <el-menu-item index="/system/admin">管理员管理</el-menu-item>
      </el-sub-menu>
      
    </el-menu>
  </el-scrollbar>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { Odometer, Document, User, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta.activeMenu) {
    return meta.activeMenu
  }
  return path
})

const variables = {
  menuBg: '#304156',
  menuText: '#bfcbd9',
  menuActiveText: '#409EFF'
}
</script>

<style scoped lang="scss">
.logo-container {
  height: 50px;
  line-height: 50px;
  text-align: center;
  color: #fff;
  background-color: #2b2f3a;
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}
.el-menu {
  border: none;
  height: 100%;
  width: 100%;
}
</style>
