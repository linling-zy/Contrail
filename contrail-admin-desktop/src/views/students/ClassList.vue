<template>
  <div class="app-container">
    <!-- 头部导航 -->
    <div class="page-header">
      <el-page-header @back="goBack" title="返回">
        <template #content>
          <span class="text-large font-600 mr-3"> 学生名单 </span>
          <span v-if="className" class="sub-title">（{{ className }}）</span>
        </template>
      </el-page-header>
    </div>

    <!-- 筛选栏 (移除部门选择) -->
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
        <el-form-item>
           <el-radio-group v-model="viewMode">
             <el-radio-button label="table">列表模式</el-radio-button>
             <el-radio-button label="card">卡片模式</el-radio-button>
           </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区域 -->
    <el-card class="table-container" v-if="viewMode === 'table'">
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" min-width="100" align="center" fixed />
        <el-table-column prop="idCard" label="身份证号" min-width="180" align="center" />
        
        <el-table-column prop="totalScore" label="综合积分" width="120" align="center" sortable>
          <template #default="{ row }">
            <span class="score-text">{{ row.totalScore }}</span>
          </template>
        </el-table-column>

        <!-- 平行状态列 -->
        <el-table-column label="初试" align="center" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status.preliminary" />
          </template>
        </el-table-column>
        <el-table-column label="体检" align="center" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status.medical" />
          </template>
        </el-table-column>
        <el-table-column label="政审" align="center" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status.political" />
          </template>
        </el-table-column>
        <el-table-column label="录取" align="center" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status.admission" />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link icon="Edit" @click="handleScore(row)">
               积分
            </el-button>
            <el-button type="primary" link icon="Setting" @click="handleEdit(row)">
              档案
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div v-else class="card-mode-wrapper">
       <el-empty v-if="!tableData.length" description="暂无数据" />
       <div v-else>
         <StudentArchive 
           :studentData="currentStudent" 
           @saved="handleCardSaved"
           @cancel="viewMode = 'table'"
         >
           <template #extra-buttons>
             <el-button @click="handlePrev" :disabled="currentIndex <= 0">上一个</el-button>
             <el-button @click="handleNext" :disabled="currentIndex >= tableData.length - 1">下一个</el-button>
           </template>
         </StudentArchive>
       </div>
    </div>

    <!-- 积分调整弹窗 -->
    <el-dialog v-model="scoreDialogVisible" title="积分调整" width="400px">
      <el-form :model="scoreForm" label-width="80px">
        <el-form-item label="学生姓名">
          <el-input v-model="scoreForm.studentName" disabled />
        </el-form-item>
        <el-form-item label="变动分值">
           <el-input-number v-model="scoreForm.value" :step="1" />
           <div class="tips">正数为加分，负数为扣分</div>
        </el-form-item>
        <el-form-item label="变动原因">
          <el-input v-model="scoreForm.reason" placeholder="请输入原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scoreDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmScore" :loading="scoreLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getStudents, updateStudentScore } from '@/api/mock/student'
import { getDepartments } from '@/api/mock/system'
import { ElMessage, ElTag } from 'element-plus'
import { Search, Setting, Edit } from '@element-plus/icons-vue'
import StudentArchive from './components/StudentArchive.vue'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const tableData = ref([])
const className = ref('')
const queryParams = reactive({
  name: '',
  classId: route.params.classId
})

const viewMode = ref('table')
const currentIndex = ref(0)
const currentStudent = computed(() => tableData.value[currentIndex.value] || {})

// 积分弹窗相关
const scoreDialogVisible = ref(false)
const scoreLoading = ref(false)
const scoreForm = reactive({
  id: null,
  studentName: '',
  value: 0,
  reason: ''
})

// 局部简单组件 StatusBadge
const StatusBadge = (props) => {
  const map = {
    qualified: { type: 'success', text: '合格' },
    failed: { type: 'danger', text: '不合格' },
    pending: { type: 'info', text: '待定' }
  }
  const conf = map[props.status] || map.pending
  return h(ElTag, { type: conf.type, effect: 'light', size: 'small' }, () => conf.text)
}

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

const getClassName = async () => {
    // 简单获取班级名称用于展示
    const res = await getDepartments()
    const cls = res.data.find(d => d.id == route.params.classId)
    if(cls) className.value = cls.name
}

const handleSearch = () => {
  getList()
  currentIndex.value = 0
}

const handleEdit = (row) => {
  router.push(`/students/status/${row.id}`)
}

const handleScore = (row) => {
  scoreForm.id = row.id
  scoreForm.studentName = row.name
  scoreForm.value = 0
  scoreForm.reason = ''
  scoreDialogVisible.value = true
}

const confirmScore = async () => {
  scoreLoading.value = true
  try {
    const res = await updateStudentScore(scoreForm.id, scoreForm.value, scoreForm.reason)
    ElMessage.success(res.message)
    scoreDialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    scoreLoading.value = false
  }
}

const goBack = () => {
  router.push('/students')
}

// Card Mode Actions
const handleCardSaved = () => {
  getList()
}

const handlePrev = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const handleNext = () => {
  if (currentIndex.value < tableData.value.length - 1) currentIndex.value++
}

watch(tableData, (newVal) => {
  if (currentIndex.value >= newVal.length) {
    currentIndex.value = 0
  }
})

onMounted(() => {
  getClassName()
  getList()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}
.sub-title {
    font-size: 14px;
    color: #909399;
}
.filter-container {
  margin-bottom: 20px;
}
.score-text {
  font-weight: bold;
  color: #409EFF;
}
.tips {
    font-size: 12px;
    color: #909399;
    margin-top: 5px;
}
</style>
