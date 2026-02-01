<template>
  <section class="app-main">
    <router-view v-slot="{ Component }">
      <transition name="fade-transform" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </section>
</template>

<style scoped>
.app-main {
  /* 50 = navbar  */
  height: calc(100vh - 50px);
  width: 100%;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--el-bg-color-page);
  transition: background-color 0.3s;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.5s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
