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
import { getStudentDetail, getStudentScoreLogs } from '@/api/student'
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
    // 获取学生详情
    const res = await getStudentDetail(Number(studentId))
    
    if (res.student) {
      const studentData = res.student
      // 转换数据格式以适配前端显示
      student.value = {
        id: studentData.id,
        name: studentData.name,
        studentNo: studentData.student_id || '',
        idCard: studentData.id_card_no || '',
        className: studentData.class_name || studentData.department?.class_name || '',
        classId: studentData.department_id || null,
        totalScore: studentData.total_score || 0,
        status: studentData.process_status || {
          preliminary: studentData.preliminary_status || 'pending',
          medical: studentData.medical_status || 'pending',
          political: studentData.political_status || 'pending',
          admission: studentData.admission_status || 'pending'
        },
        teacherEvaluation: '', // 评语需要单独获取或从最新评语中获取
        certificates: [] // 证书列表需要单独获取
      }
    } else {
      ElMessage.error('未找到学生档案')
      return
    }
    
    // 同时加载积分流水
    try {
      const logsRes = await getStudentScoreLogs(Number(studentId))
      
      if (logsRes.code === 200 && logsRes.data) {
        // 转换数据格式以适配前端显示
        scoreLogs.value = logsRes.data.items.map(item => ({
          id: item.id,
          createTime: item.create_time || item.createTime || '',
          type: item.type === 1 ? 'manual' : 'system', // 1-人工, 2-系统
          delta: item.change_amount || item.delta || 0,
          reason: item.reason || ''
        }))
      } else {
        scoreLogs.value = []
      }
    } catch (logError) {
      console.error('加载积分流水失败:', logError)
      scoreLogs.value = []
    }
  } catch (error) {
    console.error('加载学生数据失败:', error)
    ElMessage.error(error.message || '加载失败')
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
