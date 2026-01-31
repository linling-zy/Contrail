<template>
  <div class="student-profile-grid">
      <!-- 1. Enterprise Profile Header - Span 3 -->
      <div class="grid-item profile-header-card">
         <div class="header-main">
            <el-avatar :size="64" shape="square" class="profile-avatar">{{ studentData?.name?.charAt(0) }}</el-avatar>
            <div class="profile-identity">
               <div class="top-row">
                  <h1 class="name">{{ studentData?.name }}</h1>
                  <el-tag type="primary" effect="plain" size="small" class="role-tag">学生</el-tag>
               </div>
               <div class="sub-row">
                  <span class="label">学号:</span> <span class="val">{{ studentData?.studentNo }}</span>
                  <el-divider direction="vertical" />
                  <span class="label">身份证:</span> <span class="val">{{ studentData?.idCard }}</span>
               </div>
            </div>
            
            <div class="header-actions">
               <el-button type="primary" :loading="saving" @click="handleSave">保存档案</el-button>
               <slot name="extra-buttons"></slot>
            </div>
         </div>
         
         <div class="header-form">
            <el-form :inline="true" size="default" class="compact-form">
               <el-form-item label="姓名">
                  <el-input v-model="profileForm.name" />
               </el-form-item>
               <el-form-item label="学号">
                  <el-input v-model="profileForm.studentNo" />
               </el-form-item>
               <el-form-item label="身份证">
                  <el-input v-model="profileForm.idCard" />
               </el-form-item>
            </el-form>
         </div>
      </div>

      <!-- 2. Status Board - Span 2 -->
      <div class="grid-item status-board">
         <div class="card-title">状态追踪</div>
         <div class="status-table-container">
            <table class="status-table">
               <thead>
                  <tr>
                     <th>阶段</th>
                     <th>当前状态</th>
                     <th>操作</th>
                  </tr>
               </thead>
               <tbody>
                  <tr v-for="(conf, key) in statusConfigs" :key="key">
                     <td class="phase-name">{{ conf.label }}</td>
                     <td>
                        <el-tag 
                           :type="getStatusType(formStatus[key])" 
                           size="small" 
                           effect="dark"
                           class="status-pill"
                        >
                           {{ getStatusText(formStatus[key]) }}
                        </el-tag>
                     </td>
                     <td>
                        <el-radio-group v-model="formStatus[key]" size="small">
                           <el-radio-button label="qualified">合格</el-radio-button>
                           <el-radio-button label="pending">待定</el-radio-button>
                           <el-radio-button label="failed">不合格</el-radio-button>
                        </el-radio-group>
                     </td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>

      <!-- 3. Performance Card - Span 1 -->
      <div class="grid-item performance-card">
         <div class="card-title">综合积分</div>
         <div class="score-display">
            <div class="score-value">{{ studentData?.totalScore || 0 }}</div>
            <div class="score-label">当前总积分</div>
         </div>
         <el-divider class="divider-sm" />
         <div class="rank-info">
            <span>班级排名</span>
            <span class="rank-val">--</span>
         </div>
      </div>

      <!-- 4. Evaluation - Span 3 -->
      <div class="grid-item evaluation-section">
         <div class="card-title">教师评价</div>
         <el-input 
            v-model="evaluation" 
            type="textarea" 
            :rows="4" 
            placeholder="请输入教师评价..."
            resize="none"
            class="formal-textarea"
         />
      </div>
      
      <!-- 5. Certificates - Span 3 -->
      <div class="grid-item cert-section">
          <div class="card-title">荣誉证书记录</div>
          <div class="cert-table-wrapper">
             <el-table :data="displayedCertificates" border size="small" style="width: 100%" empty-text="无证书记录">
                <el-table-column prop="name" label="证书名称" />
                <el-table-column prop="date" label="提交日期" width="120" />
                <el-table-column prop="status" label="状态" width="100">
                   <template #default="{ row }">
                      <el-tag size="small" :type="row.status === 'obtained' ? 'success' : 'warning'">
                         {{ row.status === 'obtained' ? '已获得' : '审核中' }}
                      </el-tag>
                   </template>
                </el-table-column>
             </el-table>
             <div v-if="certificates.length > 2" class="expand-action" @click="isExpanded = !isExpanded">
                <el-button link type="primary" size="small">
                   {{ isExpanded ? '收起' : '展开更多' }}
                   <el-icon class="el-icon--right">
                      <ArrowUp v-if="isExpanded" />
                      <ArrowDown v-else />
                   </el-icon>
                </el-button>
             </div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { updateStudentProfile } from '@/api/mock/student'
import { ElMessage } from 'element-plus'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const props = defineProps({
  studentData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel', 'saved'])

const saving = ref(false)

// Forms
const formStatus = reactive({
  preliminary: '',
  medical: '',
  political: '',
  admission: ''
})

const profileForm = reactive({
    name: '',
    studentNo: '',
    idCard: ''
})

const evaluation = ref('')
const certificates = ref([])
const isExpanded = ref(false)

const displayedCertificates = computed(() => {
  if (isExpanded.value) return certificates.value
  return certificates.value.slice(0, 2)
})

const statusConfigs = {
  preliminary: { label: '初试' },
  medical: { label: '体检' },
  political: { label: '政审' },
  admission: { label: '录取' }
}

// Watchers
watch(() => props.studentData, (newVal) => {
  if (newVal) {
     if (newVal.status) Object.assign(formStatus, newVal.status)
     evaluation.value = newVal.teacherEvaluation || ''
     certificates.value = newVal.certificates || []
     profileForm.name = newVal.name || ''
     profileForm.studentNo = newVal.studentNo || ''
     profileForm.idCard = newVal.idCard || ''
  }
}, { immediate: true, deep: true })

const handleSave = async () => {
  if (!props.studentData?.id) return
  saving.value = true
  try {
    await updateStudentProfile(Number(props.studentData.id), {
        status: formStatus,
        teacherEvaluation: evaluation.value,
        ...profileForm
    })
    ElMessage.success('档案已保存')
    emit('saved')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// Helpers
const getStatusType = (val) => {
  const map = { qualified: 'success', failed: 'danger', pending: 'info' }
  return map[val] || 'info'
}

const getStatusText = (val) => {
  const map = { qualified: '合格', failed: '不合格', pending: '待定' }
  return map[val] || '待定'
}
</script>

<style scoped lang="scss">
$border-color: #e4e7ed;
$text-main: #303133;
$text-regular: #606266;
$bg-white: #ffffff;

.student-profile-grid {
   display: grid;
   grid-template-columns: repeat(3, 1fr);
   gap: 12px;
   font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.grid-item {
   background: $bg-white;
   border: 1px solid $border-color;
   border-radius: 4px; // Sharp professional radius
   padding: 16px;
   box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}



.card-title {
   font-size: 14px;
   font-weight: 700;
   color: $text-main;
   margin-bottom: 16px;
   border-left: 3px solid #409EFF;
   padding-left: 10px;
   line-height: 1;
}

// 1. Header
.profile-header-card {
   grid-column: span 3;
   
   .header-main {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      
      .profile-identity {
         flex: 1;
         .top-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
            .name { margin: 0; font-size: 24px; color: $text-main; }
         }
         .sub-row {
            font-size: 14px;
            color: $text-regular;
            .val { color: $text-main; font-family: monospace; }
         }
      }
      
      .header-actions {
         display: flex;
         align-items: flex-start;
      }
   }
   
   .header-form {
      background: #f9fafc;
      padding: 16px;
      border: 1px solid #EBEEF5;
      
      .compact-form {
         margin-bottom: 0;
         :deep(.el-form-item) { margin-bottom: 0; margin-right: 24px; }
      }
   }
}

// 2. Status Board
.status-board {
   grid-column: span 2;
   
   .status-table {
      width: 100%;
      border-collapse: collapse;
      
      th {
         text-align: left;
         font-size: 12px;
         color: #909399;
         padding-bottom: 8px;
         border-bottom: 1px solid #ebeef5;
      }
      
      td {
         padding: 12px 0;
         border-bottom: 1px solid #f2f6fc;
         vertical-align: middle;
      }
      
      .phase-name { font-weight: 600; font-size: 14px; color: $text-main; }
      
      tr:last-child td { border-bottom: none; }
   }
}

// 3. Performance
.performance-card {
   grid-column: span 1;
   display: flex;
   flex-direction: column;
   justify-content: center;
   
   .score-display {
      text-align: center;
      margin: 20px 0;
      .score-value {
         font-size: 48px;
         font-weight: 700;
         color: #409EFF;
         line-height: 1;
      }
      .score-label {
         font-size: 12px;
         color: #909399;
         margin-top: 4px;
      }
   }
   
   .divider-sm { margin: 12px 0; }
   
   .rank-info {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      color: $text-regular;
      .rank-val { font-weight: 600; color: $text-main; }
   }
}

// 4. Evaluation
.evaluation-section {
   grid-column: span 1;
   display: flex;
   flex-direction: column;
   
   .formal-textarea {
      flex: 1;
      :deep(.el-textarea__inner) {
         border-radius: 2px;
         background: #fcfcfc;
         height: 100%;
         min-height: 100px;
      }
   }
}

// 5. Certs
.cert-section {
   grid-column: span 2;
   padding: 16px;
   
   .cert-table-wrapper {
      border: 1px solid #ebeef5;
      
      .expand-action {
          padding: 8px;
          text-align: center;
          border-top: 1px solid #ebeef5;
          background-color: #fafafe;
          cursor: pointer;
          
          &:hover {
             background-color: #f0f2f5;
          }
      }
   }
}

</style>
