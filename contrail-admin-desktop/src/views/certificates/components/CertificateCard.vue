<template>
  <div class="certificate-entry-card">
    <el-card shadow="never">
      <div class="entry-content">
        <!-- 左侧图片 -->
        <div class="img-wrapper">
          <el-image 
            :src="data.imgUrl" 
            :preview-src-list="[data.imgUrl]"
            fit="cover"
            class="cert-img"
            preview-teleported
          />
        </div>

        <!-- 右侧信息 -->
        <div class="info-wrapper">
           <div class="header">
             <span class="cert-name">{{ data.certName }}</span>
             <el-tag :type="getStatusType(data.status)" effect="dark" size="default">
               {{ getStatusText(data.status) }}
             </el-tag>
           </div>
           
           <div class="details">
             <div class="detail-item">
               <span class="label">学生姓名：</span>
               <span class="value">{{ data.studentName }}</span>
             </div>
             <div class="detail-item">
               <span class="label">班级：</span>
               <span class="value">{{ data.className }}</span>
             </div>
             <div class="detail-item">
               <span class="label">提交时间：</span>
               <span class="value">{{ data.uploadTime }}</span>
             </div>
             <!-- 驳回原因显示 -->
             <div v-if="data.status === 2" class="detail-item reject-reason">
                <span class="label">驳回原因：</span>
                <span class="value">{{ data.rejectReason || '无' }}</span>
             </div>
           </div>

           <!-- 操作栏 -->
           <div class="actions">
             <slot name="prepend-actions"></slot>
             
             <template v-if="data.status === 0">
                <el-button type="success" size="large" @click="$emit('approve', data)" style="width: 120px">通过</el-button>
                <el-button type="danger" size="large" @click="$emit('reject', data)" style="width: 120px">驳回</el-button>
             </template>
             <template v-else>
               <span class="audited-tip">已完成审核</span>
             </template>

             <slot name="append-actions"></slot>
           </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

defineEmits(['approve', 'reject'])

const getStatusType = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger' }
  return map[status]
}

const getStatusText = (status) => {
  const map = { 0: '待审核', 1: '已通过', 2: '已驳回' }
  return map[status]
}
</script>

<style scoped lang="scss">
.certificate-entry-card {
  width: 100%;
  height: 100%;
}

:deep(.el-card__body) {
  height: 100%;
  padding: 30px;
}

.entry-content {
  display: flex;
  height: 100%;
  gap: 40px;
  
  .img-wrapper {
    flex: 1;
    min-width: 0; /* Prevent flex overflow */
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #dcdfe6;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f5f7fa;
    max-height: 600px;
    
    .cert-img {
      width: 100%;
      height: 100%;
      max-height: 600px;
    }
  }

  .info-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20px 0;
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 40px;
      
      .cert-name {
        font-size: 32px;
        font-weight: bold;
        color: #303133;
      }
    }

    .details {
      .detail-item {
        margin-bottom: 24px;
        font-size: 18px;
        line-height: 1.6;
        display: flex;
        align-items: flex-start;
        
        .label {
          color: #909399;
          width: 100px;
          flex-shrink: 0;
          text-align: right;
          margin-right: 16px;
        }
        .value {
          color: #606266;
          font-weight: 500;
          flex: 1;
        }
        
        &.reject-reason {
          .value { color: #f56c6c; }
        }
      }
    }

    .actions {
      margin-top: 60px;
      display: flex;
      gap: 24px;
      align-items: center;
      
      .audited-tip {
        color: #909399;
        font-size: 18px;
      }
    }
  }
}
</style>
