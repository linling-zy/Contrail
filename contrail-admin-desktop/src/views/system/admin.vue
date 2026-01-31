<template>
  <div class="admin-workbench">
    <!-- 1. Sidebar Panel -->
    <aside class="sidebar-panel">
      <!-- Toolbar -->
      <div class="sidebar-header">
         <h2 class="page-title">管理员管理</h2>
         <p class="subtitle">共 {{ tableData.length }} 位成员</p>
         
         <el-button type="primary" class="add-btn" icon="Plus" @click="handleAdd">
            新增管理员
         </el-button>

         <div class="search-box">
             <el-input 
               v-model="searchQuery" 
               prefix-icon="Search" 
               placeholder="搜索姓名或账号..." 
               class="formal-search" 
               clearable
             />
         </div>
      </div>

      <!-- List -->
      <div class="sidebar-content" v-loading="loading">
         <el-scrollbar>
            <div v-if="filteredTableData.length === 0" class="empty-list">
               <el-empty description="未找到管理员" :image-size="60" />
            </div>
            
            <div 
               v-for="admin in filteredTableData" 
               :key="admin.id"
               class="admin-item"
               :class="{ active: currentId === admin.id }"
               @click="handleSelect(admin)"
            >
               <el-avatar :size="40" class="avatar" :class="admin.role">
                  {{ admin.name.charAt(0) }}
               </el-avatar>
               <div class="info">
                  <div class="name-row">
                     <span class="name">{{ admin.name }}</span>
                     <el-icon v-if="admin.role === 'super'" class="super-icon"><management /></el-icon>
                  </div>
                  <div class="username">@{{ admin.username }}</div>
               </div>
               <div class="active-indicator"></div>
            </div>
         </el-scrollbar>
      </div>
    </aside>

    <!-- 2. Detail Canvas -->
    <main class="detail-canvas">
       <transition name="fade-slide" mode="out-in">
          <!-- Edit/View Mode -->
          <div v-if="currentAdmin || isCreating" :key="currentId || 'new'" class="canvas-wrapper">
             <div class="detail-card">
                <!-- Header -->
                <div class="detail-header">
                   <div class="header-main">
                      <el-avatar :size="60" shape="square" class="header-avatar">{{ form.name?.charAt(0) || '+' }}</el-avatar>
                      <div class="header-info">
                         <div class="top-row">
                             <h1 class="header-title">{{ isCreating ? '新增管理员' : form.name }}</h1>
                             <el-tag v-if="!isCreating" size="small" effect="plain" class="id-tag">ID: {{ form.id }}</el-tag>
                         </div>
                         <div class="sub-row">
                             <span>{{ isCreating ? '创建新的管理账号' : `登录账号: ${form.username}` }}</span>
                         </div>
                      </div>
                   </div>
                   <div class="header-actions">
                      <el-button 
                         v-if="!isCreating && form.username !== 'admin'" 
                         type="danger" 
                         text 
                         bg
                         @click="confirmDelete"
                      >
                         删除账号
                      </el-button>
                      <el-button type="primary" :loading="submitting" @click="submitForm">
                         {{ isCreating ? '立即创建' : '保存更改' }}
                      </el-button>
                   </div>
                </div>

                <!-- Form -->
                <div class="form-container">
                   <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="formal-form">
                      <h3 class="section-title">基本信息</h3>
                      <el-row :gutter="24">
                         <el-col :span="12">
                            <el-form-item label="真实姓名" prop="name">
                               <el-input v-model="form.name" placeholder="例如：张三" />
                            </el-form-item>
                         </el-col>
                         <el-col :span="12">
                            <el-form-item label="登录账号" prop="username">
                               <el-input 
                                  v-model="form.username" 
                                  placeholder="请输入工号或英文名" 
                                  :disabled="!isCreating"
                                  autocomplete="off"
                               />
                            </el-form-item>
                         </el-col>
                      </el-row>
                      
                      <el-form-item label="登录密码" prop="password">
                         <el-input 
                            v-model="form.password" 
                            type="password" 
                            show-password
                            :placeholder="isCreating ? '设置初始密码' : '如需修改密码请在此输入，否则留空'"
                            autocomplete="new-password"
                         />
                      </el-form-item>

                      <div class="divider-line"></div>
                      
                      <h3 class="section-title">权限配置</h3>
                      <el-form-item label="角色类型" prop="role">
                         <el-radio-group v-model="form.role" class="formal-radio-group">
                            <el-radio border label="normal">
                               <span class="radio-label">普通管理员</span>
                               <span class="radio-sub">仅管理指定部门/班级</span>
                            </el-radio>
                            <el-radio border label="super">
                               <span class="radio-label">超级管理员</span>
                               <span class="radio-sub">拥有系统所有权限</span>
                            </el-radio>
                         </el-radio-group>
                      </el-form-item>

                      <transition name="el-zoom-in-top">
                         <el-form-item v-if="form.role === 'normal'" label="管辖部门" prop="department_ids">
                            <el-select 
                               v-model="form.department_ids" 
                               multiple 
                               collapse-tags 
                               collapse-tags-tooltip
                               placeholder="请选择管辖部门"
                               style="width: 100%"
                            >
                               <el-option v-for="dept in deptList" :key="dept.id" :label="dept.name" :value="dept.id" />
                            </el-select>
                         </el-form-item>
                      </transition>
                   </el-form>
                </div>
             </div>
          </div>
          <!-- Empty State -->
          <div v-else class="empty-canvas">
              <div class="empty-content">
                 <el-icon class="empty-icon"><UserFilled /></el-icon>
                 <h3>管理员配置</h3>
                 <p>请选择左侧列表项进行操作</p>
              </div>
          </div>
       </transition>
    </main>

    <!-- Success / Delete Dialogs managed locally to ensure style -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除确认"
      width="400px"
      append-to-body
      class="formal-dialog"
    >
      <div class="delete-warning">
         <el-icon class="warning-icon"><WarningFilled /></el-icon>
         <div class="warning-text">
            <p class="main-warn">确定要删除管理员 "{{ form.name }}" 吗？</p>
            <p class="sub-warn">此操作不可恢复，该账号将无法再登录系统。</p>
         </div>
      </div>
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
import { getAdmins, createAdmin, updateAdmin, deleteAdmin, getDepartments } from '@/api/mock/system'
import { ElMessage } from 'element-plus'
import { Search, Plus, UserFilled, WarningFilled } from '@element-plus/icons-vue'

// Data
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
      const res = await getAdmins()
      tableData.value = res.data
      const deptRes = await getDepartments()
      deptList.value = deptRes.data
   } finally {
      loading.value = false
   }
}

// Handle Sidebar Select
const handleSelect = (admin) => {
   isCreating.value = false
   currentId.value = admin.id
   
   // Fill Form
   form.id = admin.id
   form.username = admin.username
   form.name = admin.name
   form.password = '' // Ensure empty
   form.role = admin.role
   form.department_ids = admin.department_ids || (admin.deptId ? [admin.deptId] : [])
}

const handleAdd = () => {
   currentId.value = null // Deselect
   isCreating.value = true
   
   // Reset Form
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
            if (!isCreating.value) { // Update
                const updateData = { ...form }
                if (!updateData.password) delete updateData.password
                await updateAdmin(updateData)
                ElMessage.success('更新成功')
            } else { // Create
                const res = await createAdmin({ ...form })
                ElMessage.success('创建成功')
            }
            isCreating.value = false
            currentId.value = null 
            loadData()
         } catch (e) {
            ElMessage.error(isCreating.value ? '创建失败' : '更新失败')
         } finally {
            submitting.value = false
         }
      }
   })
}

// Fixed: Use local Dialog instead of ElMessageBox
const confirmDelete = () => {
   deleteDialogVisible.value = true
}

const executeDelete = async () => {
   deleting.value = true
   try {
      if (form.id) {
         await deleteAdmin(form.id)
         ElMessage.success('删除成功')
         currentId.value = null
         isCreating.value = false // Reset view
         deleteDialogVisible.value = false
         loadData()
      }
   } catch (error) {
     ElMessage.error('删除失败')
   } finally {
     deleting.value = false
   }
}

// Legacy function mapping if needed by template
const handleDelete = () => confirmDelete()

onMounted(() => {
   loadData()
})
</script>

<style scoped lang="scss">
$sidebar-width: 300px;
$bg-sidebar: #ffffff;
$bg-canvas: #f2f3f5;
$primary: #409EFF;
$text-main: #303133;
$text-sub: #909399;

.admin-workbench {
  display: flex;
  height: calc(100vh - 84px);
  background: $bg-canvas;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

// Sidebar
.sidebar-panel {
  width: $sidebar-width;
  background: $bg-sidebar;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  z-index: 10;
  
  .sidebar-header {
     padding: 24px;
     border-bottom: 1px solid #f2f6fc;
     
     .page-title {
        margin: 0 0 4px 0;
        font-size: 20px;
        color: $text-main;
     }
     .subtitle {
        font-size: 13px;
        color: $text-sub;
        margin: 0 0 20px 0;
     }
     
     .add-btn {
        width: 100%;
        margin-bottom: 16px;
        border-radius: 8px;
        height: 40px;
        font-weight: 600;
     }
     
     .formal-search :deep(.el-input__wrapper) {
        border-radius: 8px;
        background: #f5f7fa;
        box-shadow: none;
        &:hover { background: white; box-shadow: 0 0 0 1px #c0c4cc inset; }
        &.is-focus { background: white; box-shadow: 0 0 0 1px $primary inset; }
     }
  }
  
  .sidebar-content {
     flex: 1;
     overflow: hidden;
     
     .admin-item {
        padding: 16px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.2s;
        border-bottom: 1px solid #fcfcfc;
        position: relative;
        
        &:hover { background: #fdfdfd; }
        &.active {
           background: #ecf5ff;
           .name { color: $primary; }
           .active-indicator { transform: scaleY(1); }
        }
        
        .avatar {
           background: #c0c4cc; 
           color: white; 
           font-weight: 600;
           &.super { background: #E6A23C; }
        }
        
        .info {
           flex: 1;
           .name-row {
              display: flex;
              align-items: center;
              gap: 6px;
              .name { font-weight: 600; color: $text-main; font-size: 14px; }
              .super-icon { color: #E6A23C; font-size: 14px; }
           }
           .username { font-size: 12px; color: $text-sub; margin-top: 2px; }
        }
        
        .active-indicator {
           position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
           background: $primary;
           transform: scaleY(0);
           transition: transform 0.2s;
        }
     }
  }
}

// Canvas
.detail-canvas {
   flex: 1;
   display: flex;
   justify-content: center;
   padding: 32px;
   overflow-y: auto;
   
   .canvas-wrapper {
      width: 100%;
      max-width: 800px;
   }
   
   .detail-card {
      background: white;
      border-radius: 4px; // Sharp professional radius
      padding: 0; // Reset padding used for header/body split
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      border: 1px solid #ebeef5;
      overflow: hidden;
   }
   
   .detail-header {
      padding: 24px 32px;
      border-bottom: 1px solid #f0f2f5;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #fdfdfd;
      
      .header-main {
         display: flex;
         gap: 20px;
         align-items: center;
         
         .header-avatar { 
            background: #409EFF; 
            font-size: 24px;
            border-radius: 4px; 
         }
         
         .header-info {
            .top-row {
               display: flex;
               align-items: center;
               gap: 12px;
               margin-bottom: 6px;
               .header-title { margin: 0; font-size: 20px; color: $text-main; }
            }
            .sub-row {
               font-size: 13px;
               color: $text-sub;
               font-family: monospace;
            }
         }
      }
   }
   
   .form-container {
      padding: 32px;
      
      .section-title {
         font-size: 14px;
         font-weight: 700;
         color: $text-main;
         margin: 0 0 20px 0;
         padding-left: 10px;
         border-left: 3px solid $primary;
         line-height: 1;
         text-transform: uppercase;
      }
      
      .divider-line {
         height: 1px;
         background: #f0f2f5;
         margin: 30px 0;
      }
      
      .formal-radio-group {
         display: flex;
         gap: 20px;
         width: 100%;
         
         .el-radio {
             flex: 1;
             height: auto;
             padding: 16px;
             margin-right: 0;
             display: flex;
             align-items: center;
             border-radius: 4px;
             
             &.is-bordered.is-checked { background-color: #ecf5ff; }
             
             .radio-label { font-weight: 600; font-size: 14px; margin-right: 8px; color: $text-main; }
             .radio-sub { font-size: 12px; color: $text-sub; }
         }
         
         :deep(.el-radio__input) {
             margin-top: 0; // vertical align fix
         }
      }
   }
}

.empty-canvas {
   display: flex;
   height: 100%;
   align-items: center;
   justify-content: center;
   color: $text-sub;
   .empty-content {
      text-align: center;
      .empty-icon { font-size: 48px; margin-bottom: 16px; color: #dcdfe6; }
      h3 { font-size: 18px; color: $text-main; margin: 0 0 8px 0; }
      p { font-size: 14px; }
   }
}

.delete-warning {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 10px 0;
    
    .warning-icon { font-size: 24px; color: #F56C6C; margin-top: 2px; }
    .warning-text {
        .main-warn { font-weight: 600; font-size: 16px; margin: 0 0 8px 0; color: #303133; }
        .sub-warn { font-size: 14px; color: #909399; margin: 0; line-height: 1.5; }
    }
}
</style>
