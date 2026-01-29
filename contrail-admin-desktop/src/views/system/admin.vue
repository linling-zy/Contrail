<template>
  <div class="app-container">
    <!-- 头部区域 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">管理员管理</h2>
        <span class="page-subtitle">共 {{ tableData.length }} 位管理员</span>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索姓名或账号..."
          prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-button type="primary" icon="Plus" @click="handleAdd" class="add-btn">
          新增管理员
        </el-button>
      </div>
    </div>

    <!-- 列表区域 -->
    <el-card shadow="never" class="table-card">
      <el-table 
        :data="filteredTableData" 
        style="width: 100%" 
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <!-- 用户信息列 (头像+姓名+账号) -->
        <el-table-column label="管理员信息" min-width="240">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar 
                :size="40" 
                :style="{ backgroundColor: getAvatarColor(row.name) }"
                class="user-avatar"
              >
                {{ row.name.charAt(0) }}
              </el-avatar>
              <div class="user-text">
                <div class="user-name">{{ row.name }}</div>
                <div class="user-account">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 角色列 -->
        <el-table-column label="角色" width="150" align="center">
          <template #default="{ row }">
            <el-tag 
              :type="row.role === 'super' ? 'warning' : 'info'"
              effect="light"
              round
              class="role-tag"
            >
              <span class="dot" :class="row.role"></span>
              {{ row.role === 'super' ? '超级管理员' : '普通管理员' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 管辖部门列 -->
        <el-table-column label="管辖部门" min-width="300">
           <template #default="{ row }">
              <span v-if="row.role === 'super'" class="text-gray">-</span>
              <template v-else>
                 <el-tooltip 
                    v-if="formatDeptNames(row.deptId).length > 30" 
                    :content="formatDeptNames(row.deptId)" 
                    placement="top"
                 >
                    <span class="dept-text truncate">{{ formatDeptNames(row.deptId) }}</span>
                 </el-tooltip>
                 <span v-else class="dept-text">{{ formatDeptNames(row.deptId) }}</span>
              </template>
           </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
             <div class="action-buttons">
                <el-tooltip content="编辑" placement="top">
                  <el-button 
                     type="primary" 
                     link 
                     class="action-btn"
                     @click="handleEdit(row)"
                  >
                     <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
                
                <el-tooltip content="删除" placement="top" v-if="row.username !== 'admin'">
                  <el-button 
                     type="danger" 
                     link 
                     class="action-btn"
                     @click="handleDelete(row)"
                  >
                     <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
             </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑管理员弹窗 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑管理员' : '新增管理员'" 
      width="480px"
      class="rounded-dialog"
    >
       <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
          <!-- 账号与姓名一行显示 -->
          <el-row :gutter="20">
             <el-col :span="12">
                <el-form-item label="登录账号" prop="username">
                   <el-input v-model="form.username" placeholder="唯一工号/英文名" />
                </el-form-item>
             </el-col>
             <el-col :span="12">
                <el-form-item label="真实姓名" prop="name">
                   <el-input v-model="form.name" placeholder="显示姓名" />
                </el-form-item>
             </el-col>
          </el-row>

          <el-form-item label="密码" prop="password" :required="!isEdit">
             <el-input 
                v-model="form.password" 
                type="password" 
                :placeholder="isEdit ? '不修改请留空' : '设置初始密码'" 
                show-password
             />
          </el-form-item>

          <el-form-item label="角色权限" prop="role">
             <div class="role-selector">
                <div 
                   class="role-card" 
                   :class="{ active: form.role === 'normal' }"
                   @click="form.role = 'normal'"
                >
                   <div class="role-icon normal"></div>
                   <span class="role-name">普通管理员</span>
                   <span class="role-desc">管理特定班级</span>
                </div>
                <div 
                   class="role-card" 
                   :class="{ active: form.role === 'super' }"
                   @click="form.role = 'super'"
                >
                   <div class="role-icon super"></div>
                   <span class="role-name">超级管理员</span>
                   <span class="role-desc">全系统权限</span>
                </div>
             </div>
          </el-form-item>

          <el-form-item 
             v-if="form.role === 'normal'" 
             label="管辖部门范围" 
             prop="department_ids"
          >
             <el-select 
                v-model="form.department_ids" 
                multiple 
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择部门..." 
                style="width: 100%"
             >
                <el-option
                   v-for="dept in deptList"
                   :key="dept.id"
                   :label="dept.name"
                   :value="dept.id"
                />
             </el-select>
          </el-form-item>
       </el-form>
       <template #footer>
          <div class="dialog-footer">
             <el-button @click="dialogVisible = false">取消</el-button>
             <el-button type="primary" @click="submitForm" :loading="submitting">
                {{ isEdit ? '保存更改' : '立即创建' }}
             </el-button>
          </div>
       </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { getAdmins, createAdmin, updateAdmin, deleteAdmin, getDepartments } from '@/api/mock/system'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const deptList = ref([])
const searchQuery = ref('')

const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

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

const rules = {
   username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
   name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
   role: [{ required: true, message: '请选择角色', trigger: 'change' }],
   department_ids: [{ required: true, message: '请选择至少一个管辖部门', trigger: 'change' }]
}

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

const formatDeptNames = (deptIds) => {
   if (!deptIds) return '-'
   const ids = Array.isArray(deptIds) ? deptIds : [deptIds]
   return ids.map(id => {
      const d = deptList.value.find(item => item.id === id)
      return d ? d.name : id
   }).join(', ')
}

const handleAdd = () => {
   isEdit.value = false
   form.id = null
   form.username = ''
   form.name = ''
   form.password = ''
   form.role = 'normal'
   form.department_ids = []
   dialogVisible.value = true
}

const handleEdit = (row) => {
   isEdit.value = true
   form.id = row.id
   form.username = row.username
   form.name = row.name
   form.password = ''
   form.role = row.role
   form.department_ids = row.department_ids || (row.deptId ? [row.deptId] : [])
   dialogVisible.value = true
}

const handleDelete = (row) => {
   ElMessageBox.confirm(`确定要删除管理员 "${row.name}" 吗?`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
   }).then(async () => {
      await deleteAdmin(row.id)
      ElMessage.success('删除成功')
      loadData()
   }).catch(() => {})
}

const submitForm = async () => {
   if (!formRef.value) return
   await formRef.value.validate(async (valid) => {
      if (valid) {
         // Manual password check for creation
         if (!isEdit.value && !form.password) {
             ElMessage.warning('请输入初始密码')
             return
         }
         
         submitting.value = true
         try {
            if (isEdit.value) {
                const updateData = { ...form }
                if (!updateData.password) delete updateData.password
                await updateAdmin(updateData)
                ElMessage.success('更新成功')
            } else {
                await createAdmin({ ...form })
                ElMessage.success('创建成功')
            }
            dialogVisible.value = false
            loadData()
         } catch (e) {
            ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
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
.app-container {
  padding: 24px;
  background-color: #f6f8f9;
  min-height: 100vh;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #1a1a1a;
      margin: 0 0 4px 0;
    }
    .page-subtitle {
      font-size: 14px;
      color: #909399;
    }
  }

  .header-right {
    display: flex;
    gap: 16px;
    align-items: center;

    .search-input {
      width: 260px;
      :deep(.el-input__wrapper) {
         box-shadow: 0 0 0 1px #e4e7ed inset; /* Subtle border */
         border-radius: 8px;
         &:hover {
            box-shadow: 0 0 0 1px #c0c4cc inset;
         }
         &.is-focus {
            box-shadow: 0 0 0 1px #409eff inset;
         }
      }
    }

    .add-btn {
      border-radius: 8px;
      padding: 10px 20px;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
      transition: transform 0.2s;
      
      &:hover {
        transform: translateY(-1px);
      }
      &:active {
        transform: translateY(0);
      }
    }
  }
}

/* Table Card */
.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  
  :deep(.el-table) {
     .el-table__row {
        height: 64px;
     }
  }
}

/* User Info */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .user-avatar {
    color: #fff;
    font-weight: 600;
    font-size: 16px;
    border: 2px solid #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  }

  .user-text {
    display: flex;
    flex-direction: column;
    
    .user-name {
      font-weight: 600;
      color: #303133;
      font-size: 15px;
    }
    .user-account {
      font-size: 12px;
      color: #909399;
      margin-top: 2px;
    }
  }
}

/* Role Tag */
.role-tag {
  border: none;
  background-color: transparent !important;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    
    &.super { background-color: #E6A23C; box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2); }
    &.normal { background-color: #409EFF; box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2); }
  }
}

/* Dept Text */
.dept-text {
  color: #606266;
  font-size: 14px;
}
.truncate {
   display: inline-block;
   max-width: 100%;
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
   vertical-align: middle;
}
.text-gray {
   color: #C0C4CC;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;

  .action-btn {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    padding: 0;
    transition: background 0.2s;
    
    &:hover {
       background-color: #f2f3f5;
    }
  }
}

/* Dialog Role Selector */
.role-selector {
   display: flex;
   gap: 16px;
   margin-bottom: 10px;

   .role-card {
      flex: 1;
      border: 1px solid #dcdfe6;
      border-radius: 8px;
      padding: 16px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.2s;
      
      .role-icon {
         width: 24px;
         height: 24px;
         border-radius: 50%;
         margin-bottom: 8px;
         &.normal { background: #409EFF; }
         &.super { background: #E6A23C; }
      }

      .role-name { font-weight: 600; color: #303133; margin-bottom: 4px; }
      .role-desc { font-size: 12px; color: #909399; }

      &:hover { border-color: #c0c4cc; }
      &.active {
         border-color: #409EFF;
         background-color: #ecf5ff;
         .role-name { color: #409EFF; }
      }
   }
}

.dialog-footer {
   display: flex;
   justify-content: flex-end;
   padding-top: 10px;
}
</style>
