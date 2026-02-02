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
                  <el-divider direction="vertical" />
                  <span class="label">学分:</span> <span class="val">{{ studentData?.credits || '--' }}</span>
                  <el-divider direction="vertical" />
                  <span class="label">绩点:</span> <span class="val">{{ studentData?.gpa || '--' }}</span>
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
               <el-form-item label="学分">
                  <el-input-number v-model="profileForm.credits" :min="0" :step="0.5" controls-position="right" style="width: 100px;" />
               </el-form-item>
               <el-form-item label="绩点">
                  <el-input-number v-model="profileForm.gpa" :min="0" :max="5" :step="0.1" controls-position="right" style="width: 100px;" />
               </el-form-item>
               <el-form-item label="籍贯">
                  <el-input v-model="profileForm.birthplace" style="width: 120px;" />
               </el-form-item>
               <el-form-item label="电话">
                  <el-input v-model="profileForm.phone" style="width: 140px;" />
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
            <el-button type="primary" link size="small" @click="openScoreDialog" style="margin-top: 8px;">调整积分</el-button>
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

      <!-- 积分调整弹窗 -->
      <el-dialog
        v-model="scoreDialogVisible"
        title="调整积分"
        width="400px"
        append-to-body
        destroy-on-close
      >
        <el-form :model="scoreForm" :rules="scoreRules" ref="scoreFormRef" label-width="80px">
           <el-form-item label="调整类型">
              <el-radio-group v-model="scoreForm.type">
                 <el-radio-button label="add">加分</el-radio-button>
                 <el-radio-button label="deduct">扣分</el-radio-button>
              </el-radio-group>
           </el-form-item>
           <el-form-item label="分值" prop="value">
              <el-input-number v-model="scoreForm.value" :min="1" :step="1" style="width: 100%" />
           </el-form-item>
           <el-form-item label="原因" prop="reason">
              <el-input
                v-model="scoreForm.reason"
                type="textarea"
                rows="3"
                placeholder="请输入调整原因（必填）"
              />
           </el-form-item>
        </el-form>
        <template #footer>
           <span class="dialog-footer">
              <el-button @click="scoreDialogVisible = false">取消</el-button>
              <el-button type="primary" :loading="scoreAdjusting" @click="confirmScoreAdjust">确定</el-button>
           </span>
        </template>
      </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { updateStudentProfile, adjustStudentScore } from '@/api/student'
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
    idCard: '',
    credits: null,
    gpa: null,
    birthplace: '',
    phone: ''
})

const scoreDialogVisible = ref(false)
const scoreAdjusting = ref(false)
const scoreFormRef = ref(null)
const scoreForm = reactive({
   type: 'add',
   value: 0,
   reason: ''
})
const scoreRules = {
   value: [{ required: true, message: '请输入分值', trigger: 'blur' }],
   reason: [{ required: true, message: '请输入原因', trigger: 'blur' }]
}

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
     // 处理状态数据（兼容后端返回的格式，将 'unqualified' 转换为前端的 'failed'）
     const mapStatus = (status) => {
       if (status === 'unqualified') return 'failed'
       return status || 'pending'
     }
     
     if (newVal.status) {
       Object.assign(formStatus, {
         preliminary: mapStatus(newVal.status.preliminary),
         medical: mapStatus(newVal.status.medical),
         political: mapStatus(newVal.status.political),
         admission: mapStatus(newVal.status.admission)
       })
     } else if (newVal.process_status) {
       // 如果后端返回的是 process_status 格式
       Object.assign(formStatus, {
         preliminary: mapStatus(newVal.process_status.preliminary),
         medical: mapStatus(newVal.process_status.medical),
         political: mapStatus(newVal.process_status.political),
         admission: mapStatus(newVal.process_status.admission)
       })
     }
     
     evaluation.value = newVal.teacherEvaluation || ''
     certificates.value = newVal.certificates || []
     profileForm.name = newVal.name || ''
     profileForm.studentNo = newVal.studentNo || newVal.student_id || ''
     profileForm.idCard = newVal.idCard || newVal.id_card_no || ''
     profileForm.credits = newVal.credits || null
     profileForm.gpa = newVal.gpa || null
     profileForm.birthplace = newVal.birthplace || ''
     profileForm.phone = newVal.phone || ''
  }
}, { immediate: true, deep: true })

const handleSave = async () => {
  if (!props.studentData?.id) return
  saving.value = true
  try {
    // 构造符合后端要求的 JSON 对象
    const requestData = {
      // 基本信息
      base_info: {
        name: profileForm.name || undefined,
        student_id: profileForm.studentNo || undefined,
        credits: profileForm.credits !== null && profileForm.credits !== '' ? profileForm.credits : undefined,
        gpa: profileForm.gpa !== null && profileForm.gpa !== '' ? profileForm.gpa : undefined,
        birthplace: profileForm.birthplace || undefined,
        phone: profileForm.phone || undefined
        // department_id 和 base_score 如果需要更新，可以从 studentData 中获取或添加输入框
      },
      // 阶段状态（将前端的 'failed' 转换为后端的 'unqualified'）
      process_status: {
        preliminary: formStatus.preliminary === 'failed' ? 'unqualified' : (formStatus.preliminary || undefined),
        medical: formStatus.medical === 'failed' ? 'unqualified' : (formStatus.medical || undefined),
        political: formStatus.political === 'failed' ? 'unqualified' : (formStatus.political || undefined),
        admission: formStatus.admission === 'failed' ? 'unqualified' : (formStatus.admission || undefined)
      },
      // 新评语（如果有内容）
      new_comment: evaluation.value && evaluation.value.trim() ? evaluation.value.trim() : undefined
    }
    
    // 移除 undefined 的字段，避免发送空值
    if (!requestData.base_info.name) delete requestData.base_info.name
    if (!requestData.base_info.student_id) delete requestData.base_info.student_id
    if (Object.keys(requestData.base_info).length === 0) {
      delete requestData.base_info
    }
    if (!requestData.new_comment) {
      delete requestData.new_comment
    }
    
    const res = await updateStudentProfile(Number(props.studentData.id), requestData)
    
    if (res.code === 200) {
      ElMessage.success(res.message || '档案已保存')
      emit('saved')
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.message || '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

// Score Adjustment Methods
const openScoreDialog = () => {
   scoreForm.type = 'add'
   scoreForm.value = 5 // Default suggestion
   scoreForm.reason = ''
   scoreDialogVisible.value = true
}

const confirmScoreAdjust = async () => {
   if (!scoreFormRef.value) return
   await scoreFormRef.value.validate(async (valid) => {
      if (valid) {
         scoreAdjusting.value = true
         try {
            const delta = scoreForm.type === 'add' ? scoreForm.value : -scoreForm.value
            const res = await adjustStudentScore(props.studentData.id, delta, scoreForm.reason)
            
            if (res.message || res.score_log) {
               ElMessage.success(res.message || '积分调整成功')
               scoreDialogVisible.value = false
               emit('saved') // Trigger refresh
            } else {
               ElMessage.error('调整失败')
            }
         } catch (error) {
            console.error('积分调整失败:', error)
            ElMessage.error(error.message || '积分调整失败')
         } finally {
            scoreAdjusting.value = false
         }
      }
   })
}

// Helpers
const getStatusType = (val) => {
  const map = { qualified: 'success', unqualified: 'danger', failed: 'danger', pending: 'info' }
  return map[val] || 'info'
}

const getStatusText = (val) => {
  const map = { qualified: '合格', unqualified: '不合格', failed: '不合格', pending: '待定' }
  return map[val] || '待定'
}
</script>

<style scoped lang="scss">
$border-color: var(--el-border-color-light);
$text-main: var(--el-text-color-primary);
$text-regular: var(--el-text-color-regular);
$bg-white: var(--el-bg-color);

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
      background: var(--el-fill-color-lighter);
      padding: 16px;
      border: 1px solid var(--el-border-color-lighter);
      
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
         color: var(--el-text-color-secondary);
         padding-bottom: 8px;
         border-bottom: 1px solid var(--el-border-color-lighter);
      }
      
      td {
         padding: 12px 0;
         border-bottom: 1px solid var(--el-border-color-lighter);
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
         background: var(--el-fill-color-lighter);
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
      border: 1px solid var(--el-border-color-lighter);
      
      .expand-action {
          padding: 8px;
          text-align: center;
          border-top: 1px solid var(--el-border-color-lighter);
          background-color: var(--el-fill-color-light);
          cursor: pointer;
          
          &:hover {
             background-color: var(--el-fill-color);
          }
      }
   }
}

</style>
