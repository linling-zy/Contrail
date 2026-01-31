<template>
  <div class="certificate-detail-panel">
    <!-- Header Section -->
    <div class="panel-header">
       <div class="heading-row">
         <h1 class="cert-title">{{ data.certName }}</h1>
         
         <div class="actions-group">
            <template v-if="data.status === 0">
               <el-button class="action-btn reject" @click="$emit('reject', data)">
                  <el-icon><Close /></el-icon> 驳回
               </el-button>
               <el-button class="action-btn approve" @click="$emit('approve', data)">
                  <el-icon><Check /></el-icon> 通过
               </el-button>
            </template>
            <div v-else class="status-badge" :class="getStatusClass(data.status)">
               <el-icon v-if="data.status === 1"><Select /></el-icon>
               <el-icon v-else><CloseBold /></el-icon>
               {{ getStatusText(data.status) }}
            </div>
         </div>
       </div>
    </div>

    <!-- Body Section (Split Layout) -->
    <div class="panel-body">
      
      <!-- Left: Visual Evidence -->
      <div class="visual-section">
        <div class="image-showcase">
          <el-image 
            :src="data.imgUrl" 
            :preview-src-list="[data.imgUrl]"
            fit="contain"
            class="main-image"
            preview-teleported
          >
             <template #placeholder>
               <div class="image-placeholder">Loading...</div>
             </template>
          </el-image>
          <div class="zoom-hint"><el-icon><ZoomIn /></el-icon> 点击查看大图</div>
        </div>
      </div>

      <!-- Right: Data Context -->
      <div class="context-section">
        <div class="section-label">申请信息</div>
        
        <div class="info-grid">
           <!-- Student Info -->
           <div class="info-card">
              <div class="icon-box blue">
                <el-icon><User /></el-icon>
              </div>
              <div class="param">
                <span class="label">申请学生</span>
                <span class="value">{{ data.studentName }}</span>
              </div>
           </div>

           <!-- Class Info -->
           <div class="info-card">
              <div class="icon-box purple">
                <el-icon><OfficeBuilding /></el-icon>
              </div>
              <div class="param">
                <span class="label">所属班级</span>
                <span class="value">{{ data.className }}</span>
              </div>
           </div>

           <!-- Time Info -->
           <div class="info-card">
              <div class="icon-box orange">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="param">
                <span class="label">提交时间</span>
                <span class="value number-font">{{ data.uploadTime }}</span>
              </div>
           </div>
        </div>

        <!-- Reject Reason Alert -->
        <transition name="el-zoom-in-top">
          <div v-if="data.status === 2" class="reject-alert">
             <div class="alert-decoration"></div>
             <div class="alert-icon-box">
               <el-icon><WarningFilled /></el-icon>
             </div>
             <div class="alert-content">
               <h4>审核驳回</h4>
               <p>{{ data.rejectReason || '未填写具体原因' }}</p>
             </div>
          </div>
        </transition>

        <!-- Approval Hint -->
        <div v-if="data.status === 1" class="approval-hint">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>证书已核验入库，积分已发放</span>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  Close, Check, Select, CloseBold, Warning, WarningFilled, 
  ZoomIn, User, OfficeBuilding, Timer, CircleCheckFilled 
} from '@element-plus/icons-vue'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

defineEmits(['approve', 'reject'])

const getStatusClass = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger' }
  return map[status]
}

const getStatusText = (status) => {
  const map = { 0: '待审核', 1: '已通过', 2: '已驳回' }
  return map[status]
}
</script>

<style scoped lang="scss">
$radius: 24px;
$bg-white: #ffffff;
$shadow: 0 16px 48px rgba(0,0,0,0.08);

.certificate-detail-panel {
  background: $bg-white;
  border-radius: $radius;
  box-shadow: $shadow;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.panel-header {
  padding: 32px 40px;
  background: #ffffff;
  border-bottom: 1px solid #f2f4f7;
  
  .heading-row {
     display: flex;
     justify-content: space-between;
     align-items: center;
     
     .cert-title {
       font-size: 28px;
       font-weight: 800;
       color: #1a1a1a;
       margin: 0;
     }
  }
}

.actions-group {
  display: flex;
  gap: 12px;
  
  .action-btn {
    padding: 10px 24px;
    height: 44px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    border: none;
    display: flex;
    gap: 6px;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    
    &.approve {
      background: #18191a; 
      color: white;
      &:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.2); }
      &:active { transform: scale(0.98); }
    }
    
    &.reject {
      background: #fff1f0;
      color: #f5222d;
      &:hover { background: #fee2e2; transform: translateY(-2px); }
      &:active { transform: scale(0.98); }
    }
  }
  
  .status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 15px;
    
    &.success { background: #effbf1; color: #27ae60; }
    &.danger { background: #fef2f2; color: #ef4444; }
  }
}

.panel-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0;
  
  .visual-section {
    flex: 5; // 50%
    background: #f8fafd;
    padding: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    border-right: 1px solid #f0f2f5;
    
    .image-showcase {
       width: 100%;
       height: 100%;
       display: flex;
       align-items: center;
       justify-content: center;
       position: relative;
       
       .main-image {
         max-width: 100%;
         max-height: 100%;
         border-radius: 12px;
         box-shadow: 0 8px 24px rgba(0,0,0,0.06);
         transition: transform 0.3s;
         &:hover { transform: scale(1.02); }
       }
       
       .zoom-hint {
         position: absolute;
         bottom: 20px;
         background: rgba(0,0,0,0.6);
         color: white;
         padding: 6px 14px;
         border-radius: 20px;
         font-size: 12px;
         display: flex;
         align-items: center;
         gap: 4px;
         backdrop-filter: blur(4px);
         opacity: 0;
         transition: opacity 0.3s;
         pointer-events: none;
       }
       
       &:hover .zoom-hint { opacity: 1; }
    }
  }
  
  .context-section {
    flex: 4; // 40%
    padding: 40px;
    background: white;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
    
    .section-label {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      color: #909399;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }
  }
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  .info-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    border-radius: 16px;
    background: #ffffff;
    border: 1px solid #f0f2f5;
    transition: all 0.2s;
    
    &:hover {
      border-color: #e4e7ed;
      box-shadow: 0 4px 12px rgba(0,0,0,0.03);
      transform: translateX(4px);
    }
    
    .icon-box {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      flex-shrink: 0;
      
      &.blue { background: #ecf5ff; color: #409EFF; }
      &.purple { background: #f4ecff; color: #9c6adc; }
      &.orange { background: #fff3e6; color: #fa8c16; }
    }
    
    .param {
      display: flex;
      flex-direction: column;
      
      .label { font-size: 13px; color: #909399; margin-bottom: 2px; }
      .value { font-size: 16px; font-weight: 600; color: #303133; }
      .number-font { font-family: 'Inter', sans-serif; font-feature-settings: "tnum"; }
    }
  }
}

.reject-alert {
  margin-top: 10px;
  position: relative;
  display: flex;
  gap: 16px;
  padding: 20px;
  background: #fff2f0;
  border-radius: 16px;
  overflow: hidden;
  
  .alert-decoration {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 6px;
    background: #ff4d4f;
  }
  
  .alert-icon-box {
    margin-left: 8px;
    width: 24px;
    height: 24px;
    color: #ff4d4f;
    font-size: 24px;
  }
  
  .alert-content {
    h4 { margin: 0 0 6px 0; color: #cf1322; font-size: 16px; font-weight: 700; }
    p { margin: 0; color: #5c0011; font-size: 14px; line-height: 1.5; opacity: 0.8; }
  }
}

.approval-hint {
  margin-top: 20px;
  padding: 16px;
  background: #f6ffed;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #52c41a;
  font-weight: 500;
  font-size: 14px;
  border: 1px dashed #b7eb8f;
}

</style>
