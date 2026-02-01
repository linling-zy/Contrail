<template>
  <div class="setup-container">
    <!-- Particle Background -->
    <Particles
      id="tsparticles"
      class="particles-bg"
      :particlesInit="particlesInit"
      :options="particlesOptions"
    />
    
    <div class="background-overlay"></div>

    <div class="content-wrapper">
      <el-card class="setup-card glass-effect">
        <template #header>
          <div class="setup-header">
            <div class="logo-box">
              <el-icon class="logo-icon"><Promotion /></el-icon>
            </div>
            <h2 class="title">系统初始化</h2>
            <p class="subtitle">Initialize Management System</p>
          </div>
        </template>
        
        <el-form 
          ref="formRef" 
          :model="form" 
          :rules="rules" 
          label-position="top"
          class="setup-form"
          @submit.prevent
        >
          <el-form-item prop="username" label="管理员账号">
            <el-input 
              v-model="form.username" 
              placeholder="设置登录账号" 
              prefix-icon="User"
              size="large"
              class="custom-input"
              autocomplete="off"
            />
          </el-form-item>
          
          <el-form-item prop="name" label="真实姓名">
            <el-input 
              v-model="form.name" 
              placeholder="例如：超级管理员" 
              prefix-icon="Avatar"
              size="large"
              class="custom-input"
              autocomplete="off"
            />
          </el-form-item>
          
          <el-form-item prop="password" label="登录密码">
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="设置强度较高的密码" 
              prefix-icon="Lock"
              show-password
              size="large"
              class="custom-input"
              autocomplete="off"
            />
          </el-form-item>
          
          <el-form-item prop="confirmPassword" label="确认密码">
            <el-input 
              v-model="form.confirmPassword" 
              type="password" 
              placeholder="再次输入密码确认" 
              prefix-icon="Lock"
              show-password
              size="large"
              class="custom-input"
              autocomplete="off"
            />
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              :loading="loading" 
              class="setup-button" 
              @click="handleSubmit"
            >
              {{ loading ? 'Initializing...' : '完成初始化' }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <div class="footer-text">
        © 2026 Contrail Aviation System. Ensuring Safety & Order.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { initializeSystem } from '@/api/system'
import { ElMessage } from 'element-plus'
import { User, Lock, Avatar, Promotion } from '@element-plus/icons-vue'
import { loadSlim } from "tsparticles-slim";

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: 'admin',
  name: '超级管理员',
  password: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validatePass2, trigger: 'blur' }]
}

/* Particles Configuration - Same as Login */
const particlesInit = async (engine) => {
  await loadSlim(engine);
};

const particlesOptions = {
  background: { color: { value: "transparent" } },
  fpsLimit: 120,
  interactivity: {
    events: {
      onClick: { enable: true, mode: "push" },
      onHover: { enable: true, mode: "grab" },
      resize: true,
    },
    modes: {
      bubble: { distance: 400, duration: 2, opacity: 0.8, size: 40 },
      push: { quantity: 4 },
      repulse: { distance: 200, duration: 0.4 },
      grab: { distance: 140, links: { opacity: 1 } }
    },
  },
  particles: {
    color: { value: "#ffffff" },
    links: { color: "#ffffff", distance: 150, enable: true, opacity: 0.2, width: 1 },
    move: { enable: true, speed: 1, direction: "none", random: false, straight: false, outModes: { default: "bounce" } },
    number: { density: { enable: true, area: 800 }, value: 60 },
    opacity: { value: 0.3 },
    shape: { type: "circle" },
    size: { value: { min: 1, max: 3 } },
  },
  detectRetina: true,
};

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await initializeSystem({
          username: form.username,
          password: form.password,
          name: form.name
        })
        
        ElMessage.success('系统初始化成功！请登录')
        // Force refresh to clear any init verification guards
        window.location.href = '/login'
      } catch (error) {
        console.error('初始化失败:', error)
        ElMessage.error(error.message || '初始化失败，请重试')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700&display=swap');

.setup-container {
  height: 100vh;
  width: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: url('@/assets/login-bg-aviation.png') no-repeat center center;
  background-size: cover;
  font-family: 'Exo 2', sans-serif;
  
  /* Force Light Mode Variables locally for consistent dark theme look */
  --el-color-primary: #00a8ff;
  --el-text-color-primary: #ffffff;
  --el-text-color-regular: #dcdde1;
  --el-text-color-placeholder:rgba(255, 255, 255, 0.5);
  --el-border-color: rgba(255, 255, 255, 0.2);
  --el-bg-color: transparent;
  color-scheme: dark; 

  .particles-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
  }

  .background-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, rgba(0, 31, 63, 0.6) 0%, rgba(0, 10, 30, 0.9) 100%);
    z-index: 2;
  }

  .content-wrapper {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    padding: 20px;
  }

  /* Glass Card */
  .setup-card {
    width: 100%;
    max-width: 500px; /* Slightly wider for the form */
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(4, 21, 39, 0.4); 
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    overflow: visible;
    transition: transform 0.3s ease;
    
    &:hover {
      transform: translateY(-5px);
      border-color: rgba(0, 168, 255, 0.3);
      box-shadow: 0 30px 60px -12px rgba(0, 168, 255, 0.15);
    }
  }
}

.setup-header {
  text-align: center;
  margin-bottom: 20px;
  margin-top: 20px;

  .logo-box {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #00a8ff 0%, #0050ef 100%);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    box-shadow: 0 10px 20px rgba(0, 168, 255, 0.3);
    
    .logo-icon {
      font-size: 32px;
      color: white;
    }
  }

  .title {
    margin: 0 0 10px;
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 300;
    letter-spacing: 2px;
    text-transform: uppercase;
  }
}

.setup-form {
  padding: 0 20px 20px;

  :deep(.el-form-item__label) {
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500;
  }

  :deep(.el-form-item) {
    margin-bottom: 24px;
  }

  /* Custom Input Styles */
  .custom-input {
    :deep(.el-input__wrapper) {
      background-color: rgba(255, 255, 255, 0.05); 
      box-shadow: none !important;
      border-bottom: 2px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px 4px 0 0;
      padding: 8px 12px;
      transition: all 0.3s;
      
      .el-input__inner {
        color: white;
        height: 40px;
        &::placeholder { color: rgba(255, 255, 255, 0.4); }
      }

      &:hover {
        background-color: rgba(255, 255, 255, 0.1);
      }

      &.is-focus {
        background-color: rgba(255, 255, 255, 0.15);
        border-bottom-color: #00a8ff;
      }
    }
    
    :deep(.el-input__prefix-inner) {
      color: rgba(255, 255, 255, 0.6); 
    }
  }
  
  /* Fix Autofill: remove shadow */
  :deep(.el-input__wrapper) input:-webkit-autofill {
      -webkit-text-fill-color: #ffffff !important;
      caret-color: white;
      transition: background-color 5000s ease-in-out 0s;
  }
}

.setup-button {
  width: 100%;
  height: 50px;
  border-radius: 25px;
  background: linear-gradient(90deg, #00a8ff 0%, #0050ef 100%);
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  box-shadow: 0 4px 15px rgba(0, 168, 255, 0.4);
  transition: all 0.3s;
  margin-top: 10px;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 168, 255, 0.6);
    background: linear-gradient(90deg, #33bfff 0%, #0066ff 100%);
  }
  
  &:active {
    transform: scale(0.98);
  }
}

.footer-text {
  margin-top: 40px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  letter-spacing: 0.5px;
}

/* Mobile Responsive */
@media (max-width: 480px) {
  .setup-card {
    max-width: 100%;
    margin: 0 10px;
  }
}
</style>
