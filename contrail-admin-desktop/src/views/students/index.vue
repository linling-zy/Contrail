<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-card class="filter-container">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="关键词">
          <el-input 
            v-model="queryParams.name" 
            placeholder="姓名 / 学号" 
            clearable 
            @keyup.enter="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区域 -->
    <el-card class="table-container">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" width="100" align="center" fixed />
        <el-table-column prop="idCard" label="身份证号" width="180" align="center" />
        <el-table-column prop="college" label="学院" width="150" align="center" />
        <el-table-column prop="className" label="班级" width="120" align="center" />
        
        <el-table-column prop="totalScore" label="综合积分" width="120" align="center" sortable>
          <template #default="{ row }">
            <span class="score-text">{{ row.totalScore }}</span>
          </template>
        </el-table-column>

        <el-table-column label="全流程状态 (初试 / 体检 / 政审 / 录取)" min-width="320" align="center">
          <template #default="{ row }">
            <div class="status-tags">
              <el-tag :type="getStatusType(row.status.preliminary)" effect="dark" class="status-item">
                初: {{ getStatusText(row.status.preliminary) }}
              </el-tag>
              <el-tag :type="getStatusType(row.status.medical)" effect="plain" class="status-item">
                体: {{ getStatusText(row.status.medical) }}
              </el-tag>
              <el-tag :type="getStatusType(row.status.political)" effect="plain" class="status-item">
                政: {{ getStatusText(row.status.political) }}
              </el-tag>
              <el-tag :type="getStatusType(row.status.admission)" effect="plain" class="status-item">
                录: {{ getStatusText(row.status.admission) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <div class="op-buttons">
              <el-button type="primary" link size="small" icon="Edit" @click="handleEdit(row)">
                状态管理
              </el-button>
              <el-button type="warning" link size="small" icon="Trophy" @click="handleScore(row)">
                奖扣分
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 状态管理抽屉 -->
    <el-drawer v-model="drawerVisible" title="全生命周期状态管理" size="400px">
      <div v-if="currStudent">
        <h3 style="margin-top:0">{{ currStudent.name }} ({{ currStudent.className }})</h3>
        <el-divider />
        <el-form :model="statusForm" label-position="top">
          <el-form-item label="初试阶段">
            <el-select v-model="statusForm.preliminary" class="w-100">
              <el-option label="合格 (Qualified)" value="qualified" />
              <el-option label="待定 (Pending)" value="pending" />
              <el-option label="不合格 (Failed)" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="体检阶段">
            <el-select v-model="statusForm.medical" class="w-100">
              <el-option label="合格 (Qualified)" value="qualified" />
              <el-option label="待定 (Pending)" value="pending" />
              <el-option label="不合格 (Failed)" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="政审阶段">
            <el-select v-model="statusForm.political" class="w-100">
              <el-option label="合格 (Qualified)" value="qualified" />
              <el-option label="待定 (Pending)" value="pending" />
              <el-option label="不合格 (Failed)" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="录取阶段">
            <el-select v-model="statusForm.admission" class="w-100">
              <el-option label="已录取 (Admitted)" value="qualified" />
              <el-option label="待定 (Pending)" value="pending" />
              <el-option label="未录取 (Rejected)" value="failed" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmStatusUpdate">保存变更</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 积分干预弹窗 -->
    <el-dialog v-model="scoreDialogVisible" title="积分干预" width="400px">
      <el-form :model="scoreForm" label-width="80px">
        <el-form-item label="学生姓名">
          <el-input v-model="scoreForm.name" disabled />
        </el-form-item>
        <el-form-item label="变动分值">
          <el-input-number v-model="scoreForm.value" :min="-100" :max="100" label="分值" />
          <div class="tip">正数为加分，负数为扣分</div>
        </el-form-item>
        <el-form-item label="变动原因">
          <el-input v-model="scoreForm.reason" type="textarea" placeholder="请输入原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scoreDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmScoreUpdate">确认执行</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getStudents, updateStudentStatus, updateStudentScore } from '@/api/mock/student'
import { ElMessage } from 'element-plus'
import { Search, Edit, Trophy } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const queryParams = reactive({
  name: ''
})

// 状态管理抽屉
const drawerVisible = ref(false)
const currStudent = ref(null)
const statusForm = reactive({
  preliminary: '',
  medical: '',
  political: '',
  admission: ''
})

// 积分弹窗
const scoreDialogVisible = ref(false)
const scoreForm = reactive({
  id: null,
  name: '',
  value: 0,
  reason: ''
})

const getList = async () => {
  loading.value = true
  try {
    const res = await getStudents(queryParams)
    tableData.value = res.data.list
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  getList()
}

// 状态显示辅助
const getStatusType = (val) => {
  const map = {
    qualified: 'success',
    failed: 'danger',
    pending: 'info'
  }
  return map[val] || 'info'
}

const getStatusText = (val) => {
  const map = {
    qualified: '合格',
    failed: '不合格',
    pending: '待定'
  }
  return map[val] || val
}

// 打开状态管理
const handleEdit = (row) => {
  currStudent.value = row
  // 浅拷贝状态
  Object.assign(statusForm, row.status)
  drawerVisible.value = true
}

const confirmStatusUpdate = async () => {
  try {
    await updateStudentStatus(currStudent.value.id, statusForm)
    ElMessage.success('状态已保存')
    drawerVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 打开积分管理
const handleScore = (row) => {
  scoreForm.id = row.id
  scoreForm.name = row.name
  scoreForm.value = 0
  scoreForm.reason = ''
  scoreDialogVisible.value = true
}

const confirmScoreUpdate = async () => {
  if (scoreForm.value === 0) {
    ElMessage.warning('分值不能为0')
    return
  }
  if (!scoreForm.reason) {
    ElMessage.warning('请输入原因')
    return
  }
  try {
    const res = await updateStudentScore(scoreForm.id, scoreForm.value, scoreForm.reason)
    ElMessage.success(res.message)
    scoreDialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  getList()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}
.filter-container {
  margin-bottom: 20px;
}
.score-text {
  font-weight: bold;
  color: #409EFF;
  font-size: 16px;
}
.status-tags {
  display: flex;
  justify-content: center;
  gap: 5px;
  
  .status-item {
    min-width: 70px;
    text-align: center;
  }
}
.w-100 {
  width: 100%;
}
.tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>
