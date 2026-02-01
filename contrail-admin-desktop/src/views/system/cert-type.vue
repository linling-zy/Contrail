<template>
  <div class="cert-immersive-container">
    <!-- Floating Header -->
    <div class="glass-header">
      <div class="brand">
        <el-icon class="brand-icon"><Postcard /></el-icon>
        <span class="brand-text">证书类型管理</span>
      </div>
      
      <el-button circle class="action-btn add-btn" @click="handleAdd">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <!-- Bento Grid Content -->
    <div class="bento-grid-wrapper">
      <div class="bento-grid">
        <div 
          v-for="(item, index) in tableData" 
          :key="item.id" 
          class="bento-card"
          :class="{ 'is-required': item.required }"
        >
          <div class="card-decoration"></div>
          
          <div class="card-content">
            <div class="card-top">
              <span class="id-badge">#{{ item.id }}</span>
              <el-tag v-if="item.required" type="danger" effect="dark" round size="small">
                必修
              </el-tag>
              <el-tag v-else type="info" effect="plain" round size="small">
                选修
              </el-tag>
            </div>

            <div class="main-info">
              <h3 class="cert-name">{{ item.name }}</h3>
            </div>

            <div class="card-footer">
               <div class="status-indicator">
                  <span class="dot" :class="{ 'active': true }"></span>
                  <span>启用中</span>
               </div>
            </div>
          </div>
        </div>
        
        <!-- Add Card Placeholder (Optional, for visual balance) -->
        <div class="bento-card add-card-placeholder" @click="handleAdd">
           <el-icon class="add-icon"><Plus /></el-icon>
           <span>添加新证书</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="新增证书类型" width="500px" class="glass-dialog">
      <el-form :model="form" ref="formRef" label-width="100px" :rules="rules">
        <el-form-item label="证书名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入证书名称" />
        </el-form-item>
        <el-form-item label="是否必填" prop="required">
          <el-switch v-model="form.required" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getCertTypes, addCertType } from '@/api/system'
import { ElMessage } from 'element-plus'
import { Postcard, Plus } from '@element-plus/icons-vue'

const tableData = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  required: false
})

const rules = {
  name: [{ required: true, message: '请输入证书名称', trigger: 'blur' }]
}

const loadData = async () => {
  try {
    const res = await getCertTypes()
    
    // 适配后端返回的数据格式
    if (res.certificate_types) {
      tableData.value = res.certificate_types.map(item => ({
        id: item.id,
        name: item.name,
        required: item.is_required !== false,
        description: item.description || ''
      }))
    } else if (res.data && Array.isArray(res.data)) {
      tableData.value = res.data
    } else {
      tableData.value = []
    }
  } catch (error) {
    console.error('加载证书类型失败:', error)
    ElMessage.error(error.message || '加载证书类型失败')
    tableData.value = []
  }
}

const handleAdd = () => {
  form.name = ''
  form.required = false
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const res = await addCertType({
          name: form.name,
          required: form.required,
          description: ''
        })
        
        if (res.message || res.certificate_type) {
          ElMessage.success(res.message || '添加成功')
          dialogVisible.value = false
          loadData()
        } else {
          ElMessage.error('添加失败：未返回有效数据')
        }
      } catch (error) {
        console.error('添加证书类型失败:', error)
        ElMessage.error(error.message || error.error || '添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.cert-immersive-container {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 20px;
  overflow-x: hidden;
  transition: background-color 0.3s;
}

/* Glass Header */
.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background: var(--el-bg-color);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  margin-bottom: 30px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .brand-icon {
    font-size: 22px;
    color: #8b5cf6; /* Purple accent */
  }
  
  .brand-text {
    font-size: 18px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #8b5cf6;
  color: white;
  box-shadow: 0 4px 10px rgba(139, 92, 246, 0.3);
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    background: #7c3aed;
  }
}

/* Bento Grid */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.bento-card {
  position: relative;
  background: var(--el-bg-color);
  border-radius: 20px;
  padding: 20px;
  height: 180px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: var(--el-box-shadow-light);
  border: 1px solid var(--el-border-color-light);
  cursor: default;
  overflow: hidden;

  &:hover {
     transform: translateY(-5px);
     box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.1);
  }

  &.is-required {
     background: var(--el-color-primary-light-9);
     border: 1px solid var(--el-color-primary-light-8);
     
     .cert-name {
        color: #5b21b6;
     }

     .card-decoration {
        background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
     }
  }
}

.card-decoration {
  position: absolute;
  top: -30px;
  right: -30px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0,0,0,0.03) 0%, transparent 70%);
  pointer-events: none;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  z-index: 1;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.id-badge {
  font-size: 12px;
  font-family: monospace;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 2px 6px;
  border-radius: 4px;
}

.main-info {
  margin: 15px 0;
  
  .cert-name {
    font-size: 20px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin: 0;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.card-footer {
   border-top: 1px solid var(--el-border-color-lighter);
   padding-top: 10px;
}

.status-indicator {
   display: flex;
   align-items: center;
   gap: 6px;
   font-size: 12px;
   color: var(--el-text-color-secondary);
   
   .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #ccc;
      
      &.active {
         background: #10b981;
         box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
      }
   }
}

.add-card-placeholder {
   border: 2px dashed var(--el-border-color);
   background: transparent;
   display: flex;
   align-items: center;
   justify-content: center;
   color: var(--el-text-color-placeholder);
   cursor: pointer;
   box-shadow: none;
   
   &:hover {
      border-color: #8b5cf6;
      color: #8b5cf6;
      background: rgba(139, 92, 246, 0.03);
      transform: translateY(-2px);
   }
   
   .add-icon {
      font-size: 32px;
      margin-bottom: 8px;
   }
}
</style>
