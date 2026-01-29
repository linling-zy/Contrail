<template>
  <div class="app-container">
    <el-card class="page-header-card">
      <template #header>
        <div class="header-row">
          <span>组织架构与证书配置</span>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索部门名称"
              prefix-icon="Search"
              clearable
              style="width: 200px; margin-right: 15px"
            />
            <el-button type="primary" icon="Plus" @click="handleAdd">添加部门</el-button>
          </div>
        </div>
      </template>
    </el-card>

    <div class="content-wrapper">
      <el-row :gutter="20">
        <el-col
          v-for="dept in filteredDepts"
          :key="dept.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          class="card-col"
        >
          <el-card shadow="hover" class="dept-card" @click="handleDetail(dept)">
            <div class="card-content">
              <div class="icon-wrapper">
                 <el-icon :size="48" color="#409EFF"><OfficeBuilding /></el-icon>
              </div>
              <h3 class="dept-name">{{ dept.name }}</h3>
              
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>


    <!-- 添加部门弹窗 -->
    <el-dialog v-model="addDialogVisible" title="添加部门" width="400px">
      <el-form :model="addForm" :rules="addRules" ref="addFormRef" label-width="80px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入部门名称" />
        </el-form-item>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getDepartments, getCertTypes, saveClassCerts, addDepartment } from '@/api/mock/system'
import { ElMessage } from 'element-plus'
import { Setting, OfficeBuilding, Plus, Search } from '@element-plus/icons-vue'

const router = useRouter()
const deptData = ref([])
const allCertTypes = ref([])
const searchQuery = ref('')

const filteredDepts = computed(() => {
  if (!searchQuery.value) return deptData.value
  return deptData.value.filter(dept => 
    dept.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 配置相关 (已移动到详情页)
// 之前逻辑已废弃，保留空壳防止报错或直接清理
// 这里直接清理

// 添加部门相关
const addDialogVisible = ref(false)
const adding = ref(false)
const addFormRef = ref(null)
const addForm = reactive({ name: '' })
const addRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const loadData = async () => {
  const deptRes = await getDepartments()
  deptData.value = deptRes.data
}

// Navigate to detail page
const handleDetail = (row) => {
  router.push(`/system/department/${row.id}`)
}

const handleAdd = () => {
  addForm.name = ''
  addDialogVisible.value = true
}

const confirmAdd = async () => {
  if (!addFormRef.value) return
  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      adding.value = true
      try {
        await addDepartment(addForm)
        ElMessage.success('添加成功')
        addDialogVisible.value = false
        loadData()
      } catch (error) {
        ElMessage.error('添加失败')
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
.app-container {
  padding: 20px;
}

.page-header-card {
  margin-bottom: 20px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-wrapper {
  /* No special styles needed for grid wrapper */
}

.card-col {
  margin-bottom: 20px;
}

.dept-card {
  height: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 32px 4px rgba(0, 0, 0, .04), 0 8px 20px rgba(0, 0, 0, .08);
  }
}

.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 10px;
  text-align: center;

  .icon-wrapper {
    background: #ecf5ff;
    padding: 20px;
    border-radius: 50%;
    margin-bottom: 20px;
  }

  .dept-name {
    margin: 0 0 20px;
    font-size: 18px;
    color: #303133;
    line-height: 1.4;
    height: 50px; /* fix height for alignment */
    overflow: hidden;
  }

  .actions {
    margin-top: 10px;
    width: 100%;
    .el-button {
      width: 80%;
    }
  }
}
</style>
