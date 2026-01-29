<template>
  <div class="student-archive">
      <!-- 档案头部 -->
      <el-card shadow="never" class="profile-card">
        <div class="profile-header">
          <el-avatar :size="64" class="avatar">{{ studentData?.name?.charAt(0) }}</el-avatar>
          <div class="info">
            <div class="name">
              {{ studentData?.name }} 
              <span class="id-card">({{ studentData?.idCard }})</span>
            </div>
            <div class="meta">
              <span>{{ studentData?.college }}</span>
              <el-divider direction="vertical" />
              <span>{{ studentData?.className }}</span>
            </div>
          </div>
          <div class="score-box">
            <div class="label">综合积分</div>
            <div class="value">{{ studentData?.totalScore }}</div>
          </div>
        </div>
      </el-card>

      <!-- 平行状态管理区 -->
      <div class="status-grid">
        <el-card 
          v-for="(conf, key) in statusConfigs" 
          :key="key" 
          shadow="hover" 
          :class="['status-card', getStatusClass(formStatus[key])]"
        >
          <template #header>
            <div class="card-header">
              <span>{{ conf.label }}</span>
              <el-tag :type="getStatusType(formStatus[key])" effect="dark" size="small">
                {{ getStatusText(formStatus[key]) }}
              </el-tag>
            </div>
          </template>
          
          <div class="card-content">
            <el-radio-group v-model="formStatus[key]" size="large" class="status-radio-group">
              <el-radio-button label="qualified">合格</el-radio-button>
              <el-radio-button label="pending">待定</el-radio-button>
              <el-radio-button label="failed">不合格</el-radio-button>
            </el-radio-group>
          </div>
        </el-card>
      </div>

      <!-- 底部操作 -->
      <div class="footer-actions">
        <slot name="extra-buttons"></slot>
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存更改</el-button>
      </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { updateStudentStatus } from '@/api/mock/student'
import { ElMessage } from 'element-plus'

const props = defineProps({
  studentData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel', 'saved'])

const saving = ref(false)

// 状态表单
const formStatus = reactive({
  preliminary: '',
  medical: '',
  political: '',
  admission: ''
})

const statusConfigs = {
  preliminary: { label: '初试阶段' },
  medical: { label: '体检阶段' },
  political: { label: '政审阶段' },
  admission: { label: '录取阶段' }
}

// Watch changes to props.studentData to update form
watch(() => props.studentData, (newVal) => {
  if (newVal && newVal.status) {
    Object.assign(formStatus, newVal.status)
  }
}, { immediate: true, deep: true })

const handleSave = async () => {
  if (!props.studentData?.id) return
  saving.value = true
  try {
    await updateStudentStatus(Number(props.studentData.id), formStatus)
    ElMessage.success('档案状态已更新')
    emit('saved')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// UI Helpers
const getStatusType = (val) => {
  const map = { qualified: 'success', failed: 'danger', pending: 'info' }
  return map[val] || 'info'
}

const getStatusText = (val) => {
  const map = { qualified: '合格', failed: '不合格', pending: '待定' }
  return map[val] || val
}

const getStatusClass = (val) => {
  return `status-${val}`
}
</script>

<style scoped lang="scss">
.profile-card {
  margin-bottom: 20px;
  .profile-header {
    display: flex;
    align-items: center;
    .avatar {
      background-color: #409EFF;
      font-size: 24px;
      margin-right: 20px;
    }
    .info {
      flex: 1;
      .name {
        font-size: 20px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 8px;
        .id-card {
          font-size: 14px;
          color: #909399;
          font-weight: normal;
          margin-left: 8px;
        }
      }
      .meta {
        color: #606266;
        font-size: 14px;
      }
    }
    .score-box {
      text-align: center;
      background: #ecf5ff;
      padding: 10px 20px;
      border-radius: 8px;
      .label {
        font-size: 12px;
        color: #409EFF;
      }
      .value {
        font-size: 24px;
        font-weight: bold;
        color: #409EFF;
      }
    }
  }
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.status-card {
  border-top: 4px solid #dcdfe6; // Default gray
  transition: all 0.3s;
  
  &.status-qualified { border-top-color: #67c23a; }
  &.status-failed { border-top-color: #f56c6c; }
  &.status-pending { border-top-color: #909399; }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }
  
  .card-content {
    display: flex;
    justify-content: center;
    padding: 10px 0;
  }
}

.status-radio-group {
  display: flex;
  width: 100%;
  :deep(.el-radio-button) {
    flex: 1;
    .el-radio-button__inner {
      width: 100%;
      padding: 10px 0;
    }
  }
}

.footer-actions {
  text-align: center;
  margin-top: 30px;
}
</style>
