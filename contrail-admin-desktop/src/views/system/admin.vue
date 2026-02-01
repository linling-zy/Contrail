<template>
  <div class="admin-immersive-container">
    <!-- 1. Floating Glass Sidebar -->
    <aside class="glass-sidebar">
      <!-- Toolbar -->
      <div class="sidebar-header">
         <div class="header-top">
            <h2 class="page-title">管理员</h2>
            <el-tag effect="dark" round size="small" type="info">{{ tableData.length }} 成员</el-tag>
         </div>
         
         <div class="search-wrapper">
             <el-input 
               v-model="searchQuery" 
               prefix-icon="Search" 
               placeholder="搜索..." 
               class="glass-input" 
               clearable
             />
             <el-button circle type="primary" class="add-btn-icon" @click="handleAdd">
                <el-icon><Plus /></el-icon>
             </el-button>
         </div>
      </div>

      <!-- List -->
      <div class="sidebar-list" v-loading="loading">
         <el-scrollbar>
            <div v-if="filteredTableData.length === 0" class="empty-list-placeholder">
               <span>无相关成员</span>
            </div>
            
            <div 
               v-for="admin in filteredTableData" 
               :key="admin.id"
               class="admin-card-item"
               :class="{ active: currentId === admin.id }"
               @click="handleSelect(admin)"
            >
               <el-avatar :size="44" class="avatar" :class="admin.role" :style="{ backgroundColor: getAvatarColor(admin.name) }">
                  {{ admin.name.charAt(0) }}
               </el-avatar>
               
               <div class="info-group">
                  <div class="name-row">
                     <span class="name">{{ admin.name }}</span>
                     <el-icon v-if="admin.role === 'super'" class="role-icon super"><Management /></el-icon>
                  </div>
                  <div class="username">@{{ admin.username }}</div>
               </div>
               
               <div class="active-glow"></div>
            </div>
         </el-scrollbar>
      </div>
    </aside>

    <!-- 2. Bento Detail Canvas -->
    <main class="detail-canvas">
       <transition name="fade-slide" mode="out-in" appear>
          <!-- Edit/View Mode -->
          <div v-if="currentAdmin || isCreating" :key="currentId || 'new'" class="bento-wrapper">
             
             <!-- Header Area -->
             <div class="canvas-header">
                <div class="title-block">
                    <h1>{{ isCreating ? '创建新账号' : '账号详情' }}</h1>
                    <p class="sub-text">{{ isCreating ? '请填写以下信息以添加新的管理员' : '查看并编辑管理员信息与权限' }}</p>
                </div>
                <div class="actions-block">
                     <el-button 
                        v-if="!isCreating && form.username !== 'admin'" 
                        type="danger" 
                        plain
                        class="glass-btn-danger"
                        @click="confirmDelete"
                     >
                        删除账号
                     </el-button>
                     <el-button type="primary" :loading="submitting" size="large" class="save-btn" @click="submitForm">
                        {{ isCreating ? '立即创建' : '保存更改' }}
                     </el-button>
                </div>
             </div>

             <!-- Bento Grid Form -->
             <div class="bento-form-grid">
                <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="full-width-form">
                   
                   <!-- Card 1: Profile Identity -->
                   <div class="bento-card profile-card">
                      <div class="card-title">身份信息</div>
                      <div class="card-body">
                         <div class="avatar-preview">
                            <el-avatar :size="80" shape="square" class="big-avatar" :style="{ backgroundColor: getAvatarColor(form.name) }">
                               {{ form.name?.charAt(0) || '+' }}
                            </el-avatar>
                         </div>
                         <div class="inputs-group">
                            <el-form-item label="真实姓名" prop="name">
                               <el-input v-model="form.name" placeholder="姓名" class="glass-input-field" />
                            </el-form-item>
                            <el-form-item label="登录账号" prop="username">
                               <el-input 
                                  v-model="form.username" 
                                  placeholder="账号" 
                                  :disabled="!isCreating"
                                  class="glass-input-field"
                               />
                            </el-form-item>
                         </div>
                      </div>
                   </div>

                   <!-- Card 2: Security -->
                   <div class="bento-card security-card">
                      <div class="card-title">安全设置</div>
                      <div class="card-body">
                         <el-form-item label="登录密码" prop="password">
                            <el-input 
                               v-model="form.password" 
                               type="password" 
                               show-password
                               :placeholder="isCreating ? '设置初始密码' : '修改密码 (留空则不修改)'"
                               class="glass-input-field"
                               autocomplete="new-password"
                            />
                         </el-form-item>
                         <p class="security-tip" v-if="!isCreating">
                            <el-icon><WarningFilled /></el-icon> 为了账号安全，建议定期更换密码。
                         </p>
                      </div>
                   </div>

                   <!-- Card 3: Permissions Layer -->
                   <div class="bento-card role-card">
                      <div class="card-title">权限配置</div>
                      <div class="card-body">
                         <el-form-item label="角色类型" prop="role">
                            <div class="role-selector">
                               <div 
                                  class="role-option" 
                                  :class="{ active: form.role === 'normal', disabled: isSelf }"
                                  @click="!isSelf && (form.role = 'normal')"
                               >
                                  <div class="role-icon"><UserFilled /></div>
                                  <div class="role-text">
                                     <span class="main">普通管理员</span>
                                     <span class="sub">仅管理特定部门</span>
                                  </div>
                               </div>
                               <div 
                                  class="role-option"
                                  :class="{ active: form.role === 'super', disabled: isSelf }"
                                  @click="!isSelf && (form.role = 'super')"
                               >
                                  <div class="role-icon"><Management /></div>
                                  <div class="role-text">
                                     <span class="main">超级管理员</span>
                                     <span class="sub">无限制访问</span>
                                  </div>
                               </div>
                            </div>
                         </el-form-item>

                         <transition name="el-zoom-in-top">
                            <el-form-item v-if="form.role === 'normal'" label="管辖部门" prop="department_ids">
                               <el-select 
                                  v-model="form.department_ids" 
                                  multiple 
                                  collapse-tags 
                                  collapse-tags-tooltip
                                  placeholder="请选择部门..."
                                  class="glass-select"
                                  popper-class="glass-popper"
                               >
                                  <el-option v-for="dept in deptList" :key="dept.id" :label="dept.name" :value="dept.id" />
                               </el-select>
                            </el-form-item>
                         </transition>
                      </div>
                   </div>
                </el-form>
             </div>
          </div>
          
          <!-- Empty State -->
          <div v-else class="empty-state-wrapper">
              <div class="empty-glass-card">
                 <el-icon class="empty-icon"><UserFilled /></el-icon>
                 <h3>选择管理员</h3>
                 <p>点击左侧列表查看详细信息或进行编辑</p>
              </div>
          </div>
       </transition>
    </main>

    <!-- Dialogs -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除确认"
      width="400px"
      append-to-body
      class="glass-dialog"
    >
       <p>确定要删除该账号吗？此操作无法撤销。</p>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="executeDelete" :loading="deleting">确认删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { getAdmins, createAdmin, updateAdmin, deleteAdmin, getDepartments, getAdminDetail } from '@/api/system'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, UserFilled, WarningFilled, Management } from '@element-plus/icons-vue'

// Data
const userStore = useUserStore()
const loading = ref(false)
const tableData = ref([])
const deptList = ref([])
const searchQuery = ref('')
const submitting = ref(false)
const formRef = ref(null)

// Workbench State
const currentId = ref(null)
const isCreating = ref(false)
const deleteDialogVisible = ref(false)
const deleting = ref(false)

const form = reactive({
   id: null,
   username: '',
   name: '',
   password: '',
   role: 'normal',
   department_ids: []
})

// Check if editing self
const isSelf = computed(() => {
   return form.id === userStore.userInfo?.id
})

// Avatar colors
const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9C27B0', '#009688', '#3F51B5']
const getAvatarColor = (name) => {
   if (!name) return colors[0]
   const index = name.charCodeAt(0) % colors.length
   return colors[index]
}

const filteredTableData = computed(() => {
   if (!searchQuery.value) return tableData.value
   const query = searchQuery.value.toLowerCase()
   return tableData.value.filter(item => 
      item.name.toLowerCase().includes(query) || 
      item.username.toLowerCase().includes(query)
   )
})

const currentAdmin = computed(() => {
   return tableData.value.find(a => a.id === currentId.value)
})

const rules = {
   username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
   name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
   role: [{ required: true, message: '请选择角色', trigger: 'change' }],
   department_ids: [{ required: true, message: '请选择至少一个管辖部门', trigger: 'change' }]
}

// Logic
const loadData = async () => {
   loading.value = true
   
   try {
      const res = await getAdmins({ per_page: 100 })
      if (res.items) {
         tableData.value = res.items.map(admin => ({
            id: admin.id,
            username: admin.username,
            name: admin.name,
            role: admin.role,
            department_ids: admin.department_ids || []
         }))
      } else if (res.data && Array.isArray(res.data)) {
         tableData.value = res.data
      } else {
         tableData.value = []
      }
   } catch (error) {
      console.error('加载管理员列表失败:', error)
      ElMessage.error(error.message || '加载管理员列表失败')
      tableData.value = []
   }
   
   try {
      const deptRes = await getDepartments({ per_page: 100 })
      let rawDepts = []
      if (deptRes.items) {
         rawDepts = deptRes.items
      } else if (deptRes.data && Array.isArray(deptRes.data)) {
         rawDepts = deptRes.data
      } else if (Array.isArray(deptRes)) {
         rawDepts = deptRes
      }
      const mappedDepts = rawDepts.map(d => ({
         ...d,
         id: Number(d.id),
         name: d.name || d.class_name || `${d.college || ''}${d.grade || ''}${d.major || ''}${d.class_name || ''}`.trim() || '未命名部门'
      }))
      deptList.value = mappedDepts
   } catch (error) {
      console.error('加载部门列表失败:', error)
      // Non-critical, just keep old list if any
   } finally {
      loading.value = false
   }
}

const handleSelect = async (admin) => {
   isCreating.value = false
   currentId.value = admin.id
   
   try {
      const res = await getAdminDetail(admin.id)
      const adminDetail = res.admin || admin
      
      form.id = adminDetail.id
      form.username = adminDetail.username
      form.name = adminDetail.name
      form.password = ''
      form.role = adminDetail.role
      form.department_ids = (adminDetail.department_ids || []).map(id => Number(id))
   } catch (error) {
       console.error('详情加载失败:', error)
      form.id = admin.id
      form.username = admin.username
      form.name = admin.name
      form.password = ''
      form.role = admin.role
      form.department_ids = (admin.department_ids || []).map(id => Number(id))
   }
}

const handleAdd = () => {
   currentId.value = null
   isCreating.value = true
   
   form.id = null
   form.username = ''
   form.name = ''
   form.password = ''
   form.role = 'normal'
   form.department_ids = []
}

const submitForm = async () => {
   if (!formRef.value) return
   await formRef.value.validate(async (valid) => {
      if (valid) {
         if (isCreating.value && !form.password) {
             ElMessage.warning('请输入初始密码')
             return
         }
         
         submitting.value = true
         try {
            if (!isCreating.value) {
                const updateData = {
                   name: form.name,
                   role: form.role,
                   department_ids: form.department_ids
                }
                if (form.password) {
                   updateData.password = form.password
                }
                const res = await updateAdmin(form.id, updateData)
                ElMessage.success(res.message || '更新成功')
            } else {
                const res = await createAdmin({
                   username: form.username,
                   password: form.password,
                   name: form.name,
                   role: form.role,
                   department_ids: form.department_ids
                })
                ElMessage.success(res.message || '创建成功')
            }
            isCreating.value = false
            currentId.value = null 
            loadData()
         } catch (error) {
            console.error('操作失败:', error)
            ElMessageBox.alert(
               error.message || error.error || (isCreating.value ? '创建失败' : '更新失败'),
               '操作提示', { confirmButtonText: '确定', type: 'warning' }
            )
         } finally {
            submitting.value = false
         }
      }
   })
}

const confirmDelete = () => {
   deleteDialogVisible.value = true
}

const executeDelete = async () => {
   deleting.value = true
   try {
      if (form.id) {
         const res = await deleteAdmin(form.id)
         ElMessage.success(res.message || '删除成功')
         currentId.value = null
         isCreating.value = false
         deleteDialogVisible.value = false
         loadData()
      }
   } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error(error.message || error.error || '删除失败')
   } finally {
     deleting.value = false
   }
}

onMounted(() => {
   loadData()
})
</script>

<style scoped lang="scss">
.admin-immersive-container {
  display: flex;
  height: calc(100vh - 84px); // Adjust based on top navbar if exists
  background: var(--el-bg-color-page);
  overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
  transition: background-color 0.3s;
}

/* 1. Floating Glass Sidebar */
.glass-sidebar {
  width: 320px;
  background: var(--el-bg-color);
  /* 性能优化：减少或移除 backdrop-filter */
  /* backdrop-filter: blur(20px); */
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  z-index: 10;
  box-shadow: var(--el-box-shadow-light);
  /* 性能优化：提示浏览器优化 */
  will-change: transform;
  
  .sidebar-header {
     padding: 24px;
     
     .header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        
        .page-title {
           margin: 0;
           font-size: 22px;
           font-weight: 800;
           color: var(--el-text-color-primary);
           letter-spacing: -0.5px;
        }
     }
     
     .search-wrapper {
        display: flex;
        gap: 12px;
     }

     .glass-input :deep(.el-input__wrapper) {
        border-radius: 12px;
        background: var(--el-fill-color-light);
        box-shadow: none !important;
        transition: all 0.2s;
        
        &:hover, &.is-focus {
           background: var(--el-bg-color-overlay);
           box-shadow: 0 0 0 2px var(--el-color-primary-light-8) !important;
        }
     }
     
     .add-btn-icon {
        width: 32px;
        height: 32px; 
        flex-shrink: 0;
     }
  }

  .sidebar-list {
     flex: 1;
     overflow: hidden;
     padding: 0 16px 16px; 
  }

  .admin-card-item {
     padding: 16px;
     margin-bottom: 8px;
     border-radius: 16px;
     background: transparent;
     display: flex;
     align-items: center;
     gap: 12px;
     cursor: pointer;
     /* 性能优化：只过渡必要的属性 */
     transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
     position: relative;
     border: 1px solid transparent;
     /* 性能优化：使用 GPU 加速 */
     will-change: background-color, transform;

     &:hover {
        background: var(--el-fill-color-light);
     }

     &.active {
        background: var(--el-bg-color-overlay);
        border-color: var(--el-color-primary-light-8);
        box-shadow: var(--el-box-shadow-light);
        
        .avatar {
           transform: scale(1.05);
        }
     }

     .avatar {
        font-weight: 700;
        color: white;
        /* 性能优化：只过渡 transform */
        transition: transform 0.15s ease;
        border: 2px solid var(--el-bg-color);
        box-shadow: var(--el-box-shadow-lighter);
        /* 性能优化：使用 GPU 加速 */
        will-change: transform;
     }

     .info-group {
        flex: 1;
        min-width: 0; 
        
        .name-row {
           display: flex;
           align-items: center;
           gap: 6px;
           margin-bottom: 4px;
           
           .name {
              font-weight: 600;
              color: var(--el-text-color-primary);
              font-size: 15px;
           }
           
           .role-icon {
              color: var(--el-color-warning);
              font-size: 14px;
           }
        }
        
        .username {
           font-size: 12px;
           color: var(--el-text-color-secondary);
           white-space: nowrap;
           overflow: hidden;
           text-overflow: ellipsis;
        }
     }
  }
}

/* 2. Bento Detail Canvas */
.detail-canvas {
   flex: 1;
   padding: 40px;
   overflow-y: auto;
   display: flex;
   justify-content: center;
   
   .bento-wrapper {
      width: 100%;
      max-width: 900px;
      /* 性能优化：移除动画，使用 transition 代替 */
      /* animation: fadeIn 0.2s ease-out; */
      /* 性能优化：使用 GPU 加速 */
      will-change: opacity, transform;
      /* 性能优化：启用硬件加速 */
      transform: translateZ(0);
   }
}

.canvas-header {
   display: flex;
   justify-content: space-between;
   align-items: flex-end;
   margin-bottom: 30px;
   
   h1 {
      font-size: 32px;
      font-weight: 800;
      color: var(--el-text-color-primary);
      margin: 0 0 8px;
      letter-spacing: -1px;
   }
   
   .sub-text {
      color: var(--el-text-color-secondary);
      margin: 0;
   }
}

.bento-form-grid {
   display: grid;
   grid-template-columns: repeat(12, 1fr);
   gap: 24px;
   
   .full-width-form {
      display: contents; /* Allow children to participate in grid */
   }
}

.bento-card {
   background: var(--el-bg-color);
   /* 性能优化：减少 backdrop-filter */
   /* backdrop-filter: blur(12px); */
   border-radius: 24px;
   border: 1px solid var(--el-border-color-light);
   box-shadow: var(--el-box-shadow-light);
   padding: 24px;
   overflow: hidden;
   /* 性能优化：使用 GPU 加速 */
   transform: translateZ(0);
   
   .card-title {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--el-text-color-secondary);
      font-weight: 700;
      margin-bottom: 20px;
   }
}

/* Specific Bento Cards */
.profile-card {
   grid-column: span 8;
   
   .card-body {
      display: flex;
      gap: 24px;
      
      .inputs-group {
         flex: 1;
         display: flex;
         flex-direction: column;
         gap: 10px;
      }
   }
}

.security-card {
   grid-column: span 4;
   
   .security-tip {
      font-size: 12px;
      color: #f59e0b;
      margin-top: 10px;
      display: flex;
      align-items: center;
      gap: 4px;
   }
}

.role-card {
   grid-column: span 12;
}

/* Role Selector Styles */
.role-selector {
   display: flex;
   gap: 20px;
   margin-bottom: 20px;
   
   .role-option {
      flex: 1;
      border: 2px solid var(--el-border-color);
      border-radius: 16px;
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 16px;
      cursor: pointer;
      /* 性能优化：只过渡必要的属性 */
      transition: border-color 0.15s ease, background-color 0.15s ease;
      /* 性能优化：使用 GPU 加速 */
      will-change: border-color, background-color;
      
      &:hover:not(.disabled) {
         border-color: var(--el-color-primary);
         background: var(--el-color-primary-light-9);
      }
      
      &.active {
         border-color: var(--el-color-primary);
         background: var(--el-color-primary-light-9);
         
         .role-icon {
            color: var(--el-color-primary);
            background: var(--el-bg-color);
            box-shadow: var(--el-box-shadow-light);
         }
      }
      
      &.disabled {
         opacity: 0.6;
         cursor: not-allowed;
         filter: grayscale(1);
      }
      
      .role-icon {
         width: 48px;
         height: 48px;
         border-radius: 12px;
         background: var(--el-fill-color);
         color: var(--el-text-color-secondary);
         display: flex;
         align-items: center;
         justify-content: center;
         font-size: 24px;
         /* 性能优化：只过渡必要的属性 */
         transition: color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
         /* 性能优化：使用 GPU 加速 */
         will-change: transform;
      }
      
      .role-text {
         display: flex;
         flex-direction: column;
         .main { font-weight: 700; color: var(--el-text-color-primary); }
         .sub { font-size: 12px; color: var(--el-text-color-secondary); }
      }
   }
}

/* Empty State */
.empty-state-wrapper {
   display: flex;
   height: 100%;
   align-items: center;
   justify-content: center;
   
   .empty-glass-card {
      background: var(--el-bg-color);
      /* 性能优化：移除 backdrop-filter */
      /* backdrop-filter: blur(8px); */
      padding: 40px 60px;
      border-radius: 30px;
      text-align: center;
      border: 1px solid var(--el-border-color-light);
      
      .empty-icon {
         font-size: 64px;
         color: var(--el-text-color-placeholder);
         margin-bottom: 16px;
      }
      h3 { margin: 0 0 8px; color: var(--el-text-color-primary); }
      p { margin: 0; color: var(--el-text-color-secondary); font-size: 14px; }
   }
}

@keyframes fadeIn {
   from { opacity: 0; transform: translateY(10px); }
   to { opacity: 1; transform: translateY(0); }
}

/* 性能优化：简化 fade-slide transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
   transition: opacity 0.15s ease-out, transform 0.15s ease-out;
   /* 性能优化：使用 GPU 加速 */
   will-change: opacity, transform;
}

.fade-slide-enter-from {
   opacity: 0;
   transform: translateY(8px);
}

.fade-slide-leave-to {
   opacity: 0;
   transform: translateY(-8px);
}

/* 性能优化：leave-active 时移除元素，避免布局抖动 */
.fade-slide-leave-active {
   position: absolute;
   width: 100%;
}

/* Glass Inputs Override */
.glass-input-field :deep(.el-input__wrapper), 
.glass-select :deep(.el-select__wrapper) {
   background: var(--el-fill-color);
   border-radius: 12px;
   box-shadow: none !important;
   border: 1px solid transparent;
   padding: 4px 12px;
   
   &:hover, &.is-focus {
      background: var(--el-bg-color);
      border-color: var(--el-border-color-hover);
      box-shadow: 0 0 0 4px var(--el-fill-color-darker) !important;
   }
}

/* Responsive */
@media (max-width: 1024px) {
    .glass-sidebar { width: 260px; }
    .bento-form-grid { grid-template-columns: 1fr; }
    .profile-card, .security-card, .role-card { grid-column: span 1; }
}
</style>
