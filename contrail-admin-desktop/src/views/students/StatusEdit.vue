<template>
  <div class="app-container">
    <el-page-header @back="goBack" content="状态档案管理" class="page-header" />

    <div v-loading="loading">
       <StudentArchive 
         v-if="student" 
         :studentData="student" 
         @cancel="goBack" 
         @saved="handleSaved" 
       >
         <template #append>
            <!-- 积分变更记录 -->
            <el-card class="score-history-card" shadow="never">
                <template #header>
                <div class="card-header">
                    <span>积分变更明细</span>
                    <el-checkbox v-model="onlyManual" label="仅显示人工干预 (隐藏系统自动加分)" size="small" />
                </div>
                </template>
                
                <el-table :data="filteredLogs" stripe style="width: 100%">
                <el-table-column prop="createTime" label="时间" width="180" />
                <el-table-column prop="type" label="类型" width="120">
                    <template #default="{ row }">
                    <el-tag v-if="row.type === 'system'" type="primary" effect="plain">系统自动</el-tag>
                    <el-tag v-else type="warning" effect="plain">人工干预</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="delta" label="变动" width="120">
                    <template #default="{ row }">
                    <span :class="row.delta > 0 ? 'score-plus' : 'score-minus'">
                        {{ row.delta > 0 ? '+' : '' }}{{ row.delta }}
                    </span>
                    </template>
                </el-table-column>
                <el-table-column prop="reason" label="原因" />
                </el-table>
            </el-card>
         </template>
       </StudentArchive>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStudents, getStudentScoreLogs } from '@/api/mock/student'
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import StudentArchive from './components/StudentArchive.vue'

const route = useRoute()
const router = useRouter()
const studentId = route.params.id

const loading = ref(false)
const student = ref(null)

// 积分流水相关
const scoreLogs = ref([])
const onlyManual = ref(false)

const filteredLogs = computed(() => {
  if (onlyManual.value) {
    return scoreLogs.value.filter(log => log.type === 'manual')
  }
  return scoreLogs.value
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getStudents({}) 
    const target = res.data.list.find(item => item.id === Number(studentId))
    if (target) {
      student.value = target
    } else {
      ElMessage.error('未找到学生档案')
    }
    // 同时加载积分流水
    const logsRes = await getStudentScoreLogs(studentId)
    scoreLogs.value = logsRes.data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleSaved = () => {
    goBack()
}

const goBack = () => {
  if (student.value && student.value.classId) {
    router.push(`/students/class/${student.value.classId}`)
  } else {
    router.push('/students')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 20px;
}

.score-history-card {
  margin-top: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }
  
  .score-plus {
    color: #67c23a;
    font-weight: bold;
  }
  
  .score-minus {
    color: #f56c6c;
    font-weight: bold;
  }
}
</style>
