<template>
  <div class="app-wrapper">
    <div class="sidebar-container">
      <Sidebar />
    </div>
    <div class="main-container">
      <Navbar />
      <AppMain />
    </div>
  </div>
</template>

<script setup>
import { Sidebar, Navbar, AppMain } from './components'
</script>

<script>
// Manual export for components index if not using unplugin-vue-components for this local dir 
// or simple re-export file. 
// For now, let's create the components/index.js to make the import above work.
</script>

<style scoped lang="scss">
.app-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
}

.sidebar-container {
  transition: width 0.28s;
  width: 210px;
  background-color: var(--el-bg-color);
  height: 100%;
  position: fixed;
  font-size: 0;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 1001;
  overflow: hidden;
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
  transition: background-color 0.3s;
}

.main-container {
  height: 100vh;
  transition: margin-left 0.28s;
  margin-left: 210px;
  width: calc(100% - 210px);
  position: relative;
  overflow: hidden;
}
</style>
