<template>
  <div class="theme-switch">
    <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到暗黑模式'" placement="bottom">
      <el-button
        :icon="isDark ? Sunny : Moon"
        circle
        @click="handleToggle"
        class="theme-toggle-btn"
      />
    </el-tooltip>
  </div>
</template>

<script setup>
import { nextTick } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { Sunny, Moon } from '@element-plus/icons-vue'

const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: ''
})

const toggleDark = useToggle(isDark)

const handleToggle = (event) => {
  const x = event.clientX
  const y = event.clientY
  const endRadius = Math.hypot(
    Math.max(x, innerWidth - x),
    Math.max(y, innerHeight - y),
  )

  if (!document.startViewTransition) {
    toggleDark()
    return
  }

  const transition = document.startViewTransition(async () => {
    toggleDark()
    await nextTick()
  })

  transition.ready.then(() => {
    // 新视图总是从按钮位置圆形扩散（从 0 到 endRadius）
    const clipPath = [
      `circle(0px at ${x}px ${y}px)`,
      `circle(${endRadius}px at ${x}px ${y}px)`,
    ]
    
    // 对新视图应用圆形扩散动画
    const root = document.documentElement
    const animation = root.animate(
      {
        clipPath: clipPath,
      },
      {
        duration: 400,
        easing: 'ease-in',
        pseudoElement: '::view-transition-new(root)',
      },
    )
  })
}
</script>

<style scoped lang="scss">
.theme-switch {
  display: flex;
  align-items: center;
  margin-right: 15px;

  .theme-toggle-btn {
    transition: all 0.3s ease;
    border: none;
    background: transparent;
    
    &:hover {
      transform: scale(1.1);
    }
  }
}
</style>

<style lang="scss">
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

// 新视图始终在上层，无论什么情况
::view-transition-new(root) {
  z-index: 9999 !important;
}

// 旧视图始终在下层
::view-transition-old(root) {
  z-index: 1 !important;
}
</style>