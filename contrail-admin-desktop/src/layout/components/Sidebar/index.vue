<template>
  <el-scrollbar wrap-class="scrollbar-wrapper">
    <el-menu
      :default-active="activeMenu"
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


</script>

<style scoped lang="scss">
.logo-container {
  height: 50px;
  line-height: 50px;
  text-align: center;
  color: var(--el-text-color-primary);
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }
}
.el-menu {
  border: none;
  height: 100%;
  width: 100%;
  padding-top: 8px;
  background-color: var(--el-bg-color);
}

:deep(.el-menu-item) {
  margin: 4px 8px;
  border-radius: 6px;
  height: 48px;
  line-height: 48px;
  color: var(--el-text-color-regular);
  
  &:hover {
    background-color: var(--el-fill-color-light) !important;
    color: var(--el-text-color-primary);
  }
  
  &.is-active {
    background-color: var(--el-color-primary-light-9) !important;
    color: var(--el-color-primary);
    position: relative;
    font-weight: 600;
  }

  /* Adjust icon size and spacing if needed */
  .el-icon {
    margin-right: 12px;
    font-size: 18px;
  }
}
 
:deep(.el-sub-menu__title) {
  color: var(--el-text-color-regular);
  
  &:hover {
    background-color: var(--el-fill-color-light) !important;
    color: var(--el-text-color-primary);
  }
}
</style>
