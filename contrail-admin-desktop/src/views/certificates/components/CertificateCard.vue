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

        <!-- Dynamic Specs Section -->
        <div v-if="displayItems.length > 0" class="specs-section">
          <div class="section-label">详细信息</div>
          <div class="details-grid" :class="gridClass">
             <div 
               v-for="(item, idx) in displayItems" 
               :key="idx" 
               class="detail-cell"
               :class="{ 'highlight': item.highlight, 'full-width': item.fullWidth }"
             >
                <div class="cell-label">
                  <el-icon v-if="item.icon" class="cell-icon"><component :is="item.icon" /></el-icon>
                  {{ item.label }}
                </div>
                <div class="cell-value">
                   <template v-if="item.tags">
                      <el-tag 
                        v-for="(tag, tIdx) in item.tags" 
                        :key="tIdx" 
                        size="small" 
                        effect="dark"
                        :type="tag.type || 'primary'"
                        class="detail-tag"
                      >
                        {{ tag.text }}
                      </el-tag>
                   </template>
                   <span v-else>{{ item.value }}</span>
                </div>
             </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  Close, Check, Select, CloseBold, Warning, WarningFilled, 
  ZoomIn, User, OfficeBuilding, Timer, CircleCheckFilled,
  Trophy, Medal, Management, DataAnalysis, Flag
} from '@element-plus/icons-vue'
import { computed } from 'vue'

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

// *** Dynamic Display Logic ***
const displayItems = computed(() => {
  const extra = props.data.extraData || {};
  const list = [];
  
  // Helper to check existence
  const has = (key) => extra[key] !== undefined && extra[key] !== null && extra[key] !== '';

  // Type A: CET (English 4/6) - Check 'score'
  if (has('score')) {
    list.push({ 
      label: '考试分数', 
      value: extra.score, 
      highlight: true, 
      icon: 'DataAnalysis' 
    });
  }
  
  // Type B: IELTS - Check 'listening' or 'reading' (Sub-scores)
  else if (has('listening') || has('reading')) {
    if (has('total')) {
       list.push({ label: '总成绩', value: extra.total, highlight: true, icon: 'Trophy', fullWidth: true });
    }
    const subs = [
      { k: 'listening', l: '听力' }, { k: 'reading', l: '阅读' },
      { k: 'writing', l: '写作' }, { k: 'speaking', l: '口语' }
    ];
    subs.forEach(sub => {
       if (has(sub.k)) list.push({ label: sub.l, value: extra[sub.k] });
    });
  }
  
  // Type C: Job Experience - Check 'position'
  else if (has('position')) {
    list.push({ label: '担任职务', value: extra.position, highlight: true, icon: 'Management', fullWidth: true });
    if (has('date')) {
      list.push({ label: '任职时间', value: extra.date, icon: 'Timer', fullWidth: true });
    }
    if (has('award')) {
      list.push({ label: '集体获奖', value: extra.award, icon: 'Medal' });
    }
  }
  
  // Type D: Awards - Check 'rank' or 'level'
  else if (has('rank') || has('level') || has('organizer')) {
    // Combine Level and Rank into Tags
    const tags = [];
    if (has('level')) tags.push({ text: extra.level, type: 'danger' });
    if (has('rank')) tags.push({ text: extra.rank, type: 'warning' });
    
    if (tags.length > 0) {
      list.push({ label: '获奖等级', tags: tags, icon: 'Trophy', fullWidth: true });
    }
    
    if (has('organizer')) {
      list.push({ label: '主办单位', value: extra.organizer, icon: 'Flag', fullWidth: true });
    }
    if (has('date')) {
      list.push({ label: '获奖时间', value: extra.date, icon: 'Timer' });
    }
  }
  
  return list;
});

const gridClass = computed(() => {
   // Adjust grid layout based on item count for prettier display
   const count = displayItems.value.length;
   if (count <= 1) return 'single-col';
   return ''; // Default 2 cols
});
</script>

<style scoped lang="scss">
$radius: 24px;
$bg-white: var(--el-bg-color);
$shadow: var(--el-box-shadow-light);

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
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  
  .heading-row {
     display: flex;
     justify-content: space-between;
     align-items: center;
     
     .cert-title {
       font-size: 28px;
       font-weight: 800;
       color: var(--el-text-color-primary);
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
      background: var(--el-text-color-primary); 
      color: var(--el-bg-color);
      &:hover { transform: translateY(-2px); box-shadow: var(--el-box-shadow); }
      &:active { transform: scale(0.98); }
    }
    
    &.reject {
      background: var(--el-color-danger-light-9);
      color: var(--el-color-danger);
      &:hover { background: var(--el-color-danger-light-8); transform: translateY(-2px); }
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
    
    &.success { background: var(--el-color-success-light-9); color: var(--el-color-success); }
    &.danger { background: var(--el-color-danger-light-9); color: var(--el-color-danger); }
  }
}

.panel-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0;
  
  .visual-section {
    flex: 5; // 50%
    background: var(--el-fill-color-light);
    padding: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    border-right: 1px solid var(--el-border-color-light);
    
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
    background: var(--el-bg-color);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
    
    .section-label {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--el-text-color-secondary);
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
    background: var(--el-bg-color-overlay);
    border: 1px solid var(--el-border-color-light);
    transition: all 0.2s;
    
    &:hover {
      border-color: var(--el-border-color-hover);
      box-shadow: var(--el-box-shadow-light);
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
      
      &.blue { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
      &.purple { background: var(--el-color-primary-light-8); color: var(--el-color-primary-dark-2); }
      &.orange { background: var(--el-color-warning-light-9); color: var(--el-color-warning); }
    }
    
    .param {
      display: flex;
      flex-direction: column;
      
      .label { font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 2px; }
      .value { font-size: 16px; font-weight: 600; color: var(--el-text-color-primary); }
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
  background: var(--el-color-danger-light-9);
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
    color: var(--el-color-danger);
    font-size: 24px;
  }
  
  .alert-content {
    h4 { margin: 0 0 6px 0; color: var(--el-color-danger-dark-2); font-size: 16px; font-weight: 700; }
    p { margin: 0; color: var(--el-color-danger); font-size: 14px; line-height: 1.5; opacity: 0.8; }
  }
}

.approval-hint {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-color-success-light-9);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--el-color-success);
  font-weight: 500;
  font-size: 14px;
  border: 1px dashed var(--el-color-success-light-5);
}

.specs-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    
    &.single-col { grid-template-columns: 1fr; }
    
    .detail-cell {
      background: var(--el-fill-color-light);
      border-radius: 12px;
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      border: 1px solid transparent;
      
      &.full-width { grid-column: span 2; }
      
      &.highlight {
        background: var(--el-color-primary-light-9);
        border-color: var(--el-color-primary-light-8);
        
        .cell-value {
           font-size: 24px;
           color: var(--el-color-primary);
           font-weight: 800;
        }
      }
      
      .cell-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        display: flex;
        align-items: center;
        gap: 6px;
        
        .cell-icon { font-size: 14px; opacity: 0.8; }
      }
      
      .cell-value {
        font-size: 15px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        word-break: break-word;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      
      .detail-tag {
        font-weight: 600;
      }
    }
  }
}

</style>
