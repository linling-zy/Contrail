<template>
  <div class="department-immersive-container">
    <!-- Floating Header / Action Bar -->
    <div class="glass-header">
      <div class="brand">
        <el-icon class="brand-icon"><OfficeBuilding /></el-icon>
        <span class="brand-text">组织架构</span>
      </div>
      
      <div class="actions-group">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input 
            v-model="searchQuery" 
            placeholder="搜索部门..." 
            class="transparent-input"
          />
        </div>
        <el-button circle class="action-btn add-btn" @click="handleAdd">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Bento Grid Content -->
    <div class="bento-grid-wrapper">
      <div class="bento-grid">
        <div 
          v-for="(dept, index) in filteredDepts" 
          :key="dept.id" 
          class="bento-card"
          :class="getCardClass(index)"
          @click="openDetail(dept)"
        >
          <div class="card-bg-decoration"></div>
          <div class="card-content">
            <div class="card-header">
              <span class="dept-badge">{{ dept.college || '未分配学院' }}</span>
              <el-icon class="arrow-icon"><Right /></el-icon>
            </div>
            
            <div class="main-info">
              <h2 class="dept-title">{{ dept.name }}</h2>
              <p class="dept-meta">
                <span v-if="dept.grade">{{ dept.grade }}</span>
                <span v-if="dept.major"> · {{ dept.major }}</span>
              </p>
            </div>

            <div class="stat-row">
              <div class="stat-item">
                <span class="stat-label">班级成员</span>
                <span class="stat-val">{{ dept.studentCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">证书配置</span>
                <span class="stat-val">{{ dept.certCount }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Master-Detail Drawer -->
    <el-drawer
      v-model="drawerVisible"
      title="部门详情"
      :size="drawerSize"
      :with-header="false"
      destroy-on-close
      class="glass-drawer"
    >
      <div class="drawer-handler" @click="closeDetail">
         <el-icon><Close /></el-icon>
      </div>
      <department-detail 
        v-if="selectedDeptId" 
        :dept-id="selectedDeptId" 
        @close="closeDetail"
      />
    </el-drawer>

    <!-- Keep Add Dialog as is for now, or style it up similarly if desired later -->
    <el-dialog v-model="addDialogVisible" title="添加部门" width="500px" class="glass-dialog">
      <!-- ... existing dialog content ... -->
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="100px">
        <el-form-item label="学院" prop="college">
          <el-input v-model="addForm.college" placeholder="请输入学院名称" />
        </el-form-item>
        <el-form-item label="年级" prop="grade">
          <el-input v-model="addForm.grade" placeholder="请输入年级，如：2023级" />
        </el-form-item>
        <el-form-item label="专业" prop="major">
          <el-input v-model="addForm.major" placeholder="请输入专业名称" />
        </el-form-item>
        <el-form-item label="班级" prop="class_name">
          <el-input v-model="addForm.class_name" placeholder="请输入班级名称，如：2301班" />
        </el-form-item>
        <el-form-item label="加分起始日期" prop="bonus_start_date">
          <el-date-picker
            v-model="addForm.bonus_start_date"
            type="date"
            placeholder="选择加分起始日期（可选）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="基础分" prop="base_score">
          <el-input-number v-model="addForm.base_score" :min="0" :max="100" placeholder="默认80" style="width: 100%" />
        </el-form-item>
        <el-alert
          title="提示：至少需要填写学院、年级、专业、班级中的一项"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAdd" :loading="adding">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { getDepartments, addDepartment } from '@/api/system'
import { ElMessage } from 'element-plus'
import { Setting, OfficeBuilding, Plus, Search, Right, Close } from '@element-plus/icons-vue'

// Async import for circular dependency avoidance if any, or just good practice
import DepartmentDetail from './department-detail.vue'

const router = useRouter()
const deptData = ref([])
const allCertTypes = ref([])
const searchQuery = ref('')
const selectedDeptId = ref(null)
const drawerVisible = ref(false)
const drawerSize = ref('600px') // Responsive?

const filteredDepts = computed(() => {
  if (!searchQuery.value) return deptData.value
  return deptData.value.filter(dept => 
    dept.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// Randomized-looking but deterministic layout for Bento Grid
const getCardClass = (index) => {
  // Simple pattern repeater: Small, Small, Wide, Large, Small...
  const pattern = ['span-1', 'span-1', 'span-2-wide', 'span-2-tall', 'span-1', 'span-1'];
  return pattern[index % pattern.length];
}

const openDetail = (row) => {
  selectedDeptId.value = row.id
  drawerVisible.value = true
}

const closeDetail = () => {
    drawerVisible.value = false
    // Clear after animation if possible, but immediate is fine for now
    // selectedDeptId.value = null 
    loadData() // Reload list to reflect changes
}

// 配置相关 (已移动到详情页)
// 之前逻辑已废弃，保留空壳防止报错或直接清理
// 这里直接清理

// 添加部门相关
const addDialogVisible = ref(false)
const adding = ref(false)
const addFormRef = ref(null)
const addForm = reactive({
  college: '',
  grade: '',
  major: '',
  class_name: '',
  bonus_start_date: '',
  base_score: 80
})

// 禁用今天之前的日期
const disabledDate = (time) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return time.getTime() < today.getTime()
}

// 自定义验证：至少需要填写一个字段
const validateAtLeastOne = (rule, value, callback) => {
  const hasValue = addForm.college || addForm.grade || addForm.major || addForm.class_name
  if (!hasValue) {
    callback(new Error('至少需要填写学院、年级、专业、班级中的一项'))
  } else {
    callback()
  }
}

const addRules = {
  college: [{ validator: validateAtLeastOne, trigger: 'blur' }],
  grade: [{ validator: validateAtLeastOne, trigger: 'blur' }],
  major: [{ validator: validateAtLeastOne, trigger: 'blur' }],
  class_name: [{ validator: validateAtLeastOne, trigger: 'blur' }],
  base_score: [
    { required: true, message: '请输入基础分', trigger: 'blur' },
    { type: 'number', min: 0, message: '基础分必须为非负整数', trigger: 'blur' }
  ]
}

const loadData = async () => {
  try {
    const res = await getDepartments({ per_page: 100 })
    
    // 适配后端返回的数据格式：{ total, page, per_page, pages, items }
    if (res.items) {
      deptData.value = res.items.map(dept => ({
        id: dept.id,
        name: dept.class_name || `${dept.college || ''}${dept.grade || ''}${dept.major || ''}${dept.class_name || ''}`.trim() || '未命名部门',
        college: dept.college,
        grade: dept.grade,
        major: dept.major,
        className: dept.class_name,
        studentCount: dept.student_count || 0,
        certCount: dept.certificate_types_count !== undefined ? dept.certificate_types_count : (dept.certificate_types ? dept.certificate_types.length : 0)
      }))
    } else if (res.data && Array.isArray(res.data)) {
      // Mock 数据格式（兼容）
      deptData.value = res.data
    } else {
      deptData.value = []
    }
  } catch (error) {
    console.error('加载部门列表失败:', error)
    ElMessage.error(error.message || '加载部门列表失败')
    deptData.value = []
  }
}

// Navigate to detail page - OLD, replaced by drawer
// const handleDetail = (row) => {
//   router.push(`/system/department/${row.id}`)
// }

const handleAdd = () => {
  addForm.college = ''
  addForm.grade = ''
  addForm.major = ''
  addForm.class_name = ''
  addForm.bonus_start_date = ''
  addForm.base_score = 80
  addDialogVisible.value = true
}

const confirmAdd = async () => {
  if (!addFormRef.value) return
  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      // 验证至少有一个字段不为空
      const hasValue = addForm.college || addForm.grade || addForm.major || addForm.class_name
      if (!hasValue) {
        ElMessage.warning('至少需要填写学院、年级、专业、班级中的一项')
        return
      }
      
      adding.value = true
      try {
        // 构建请求数据，只发送非空字段
        const requestData = {}
        if (addForm.college) requestData.college = addForm.college
        if (addForm.grade) requestData.grade = addForm.grade
        if (addForm.major) requestData.major = addForm.major
        if (addForm.class_name) requestData.class_name = addForm.class_name
        if (addForm.bonus_start_date) requestData.bonus_start_date = addForm.bonus_start_date
        if (addForm.base_score !== undefined) requestData.base_score = addForm.base_score
        
        const res = await addDepartment(requestData)
        
        if (res.message || res.department) {
          ElMessage.success(res.message || '添加成功')
          addDialogVisible.value = false
          loadData()
        } else {
          ElMessage.error('添加失败：未返回有效数据')
        }
      } catch (error) {
        console.error('添加部门失败:', error)
        ElMessage.error(error.message || error.error || '添加失败')
      } finally {
        adding.value = false
      }
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
/* Google Fonts import would go in index.html, assume font-family inheritance */

.department-immersive-container {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 20px;
  position: relative;
  overflow-x: hidden;
  transition: background-color 0.3s;
}

/* Glass Header */
.glass-header {
  position: sticky;
  top: 10px;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background: var(--el-bg-color);
  backdrop-filter: blur(16px);
  border-radius: 20px;
  box-shadow: var(--el-box-shadow-light);
  border: 1px solid var(--el-border-color-light);
  margin-bottom: 30px;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: var(--el-box-shadow);
    background: var(--el-bg-color-overlay);
  }
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .brand-icon {
    font-size: 24px;
    color: #3b82f6;
  }
  
  .brand-text {
    font-size: 20px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    letter-spacing: -0.5px;
  }
}

.actions-group {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-box {
  display: flex;
  align-items: center;
  background: var(--el-fill-color);
  padding: 8px 16px;
  border-radius: 12px;
  transition: all 0.3s;
  
  &:focus-within {
    background: var(--el-bg-color);
    box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
  }
  
  .search-icon {
    color: var(--el-text-color-placeholder);
    margin-right: 8px;
  }
  
  .transparent-input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 14px;
    width: 180px;
    color: var(--el-text-color-primary);
    
    &::placeholder {
      color: var(--el-text-color-placeholder);
    }
  }
}

.action-btn {
  width: 42px;
  height: 42px;
  border: none;
  background: #3b82f6;
  color: white;
  box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39);
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45);
    background: #2563eb;
  }
  
  &:active {
    transform: translateY(0);
  }
}

/* Bento Grid */
.bento-grid-wrapper {
  padding: 10px;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  grid-auto-flow: dense;
}

.bento-card {
  position: relative;
  background: var(--el-bg-color);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  &:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: var(--el-box-shadow);
    z-index: 10;
    
    .arrow-icon {
       transform: translateX(4px);
       opacity: 1;
    }
  }

  /* Span Classes */
  &.span-2-wide {
    grid-column: span 2;
    background: var(--el-bg-color);
  }
  
  &.span-2-tall {
    grid-row: span 2;
    background: var(--el-bg-color);
  }
}

.card-bg-decoration {
  position: absolute;
  top: -50px;
  right: -50px;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, rgba(255, 255, 255, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
}

.card-content {
  position: relative;
  h2 {
    margin: 0;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.dept-badge {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.arrow-icon {
  opacity: 0;
  transition: all 0.3s;
  color: #94a3b8;
}

.main-info {
  margin-bottom: 30px;
  
  .dept-title {
    font-size: 28px;
    font-weight: 800;
    color: var(--el-text-color-primary);
    margin-bottom: 8px;
    line-height: 1.2;
    letter-spacing: -0.5px;
  }
  
  .dept-meta {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.stat-row {
  display: flex;
  gap: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(0,0,0,0.04);
}

.stat-item {
  display: flex;
  flex-direction: column;
  
  .stat-label {
    font-size: 11px;
    text-transform: uppercase;
    color: var(--el-text-color-secondary);
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
  
  .stat-val {
    font-size: 18px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }
}

/* Responsive adjustments for spans */
@media (max-width: 768px) {
  .bento-card.span-2-wide,
  .bento-card.span-2-tall {
    grid-column: span 1;
    grid-row: span 1;
  }
  
  .glass-header {
     padding: 10px 15px;
     flex-direction: column;
     gap: 15px;
     align-items: stretch;
     
     .actions-group {
        justify-content: space-between;
     }
     
     .search-box {
        flex: 1;
        width: auto;
        
        .transparent-input {
           width: 100%;
        }
     }
  }
}

/* Custom Drawer Styles override */
:deep(.el-drawer) {
    background: var(--el-bg-color-overlay) !important;
    backdrop-filter: blur(20px);
    box-shadow: -10px 0 40px rgba(0, 0, 0, 0.1);
}

.drawer-handler {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 201; /* Above drawer content */
    cursor: pointer;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
        background: var(--el-fill-color-dark);
        transform: rotate(90deg);
    }
}

</style>
