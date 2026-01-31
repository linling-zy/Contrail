<template>
  <div class="workbench-container">
    <!-- Left Sidebar: The List -->
    <aside class="sidebar-panel">
      <!-- Sidebar Header: Filters -->
      <div class="sidebar-header">
        <h2 class="sidebar-title">证书审核</h2>
        <div class="filter-group">
          <el-input 
            v-model="searchText" 
            placeholder="搜索学生或证书..." 
            prefix-icon="Search"
            clearable
            class="modern-search"
          />
          <el-dropdown trigger="click" @command="handleStatusFilter" class="filter-dropdown">
            <el-button circle class="filter-btn">
              <el-icon><Filter /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="" :class="{ active: queryParams.status === '' }">全部状态</el-dropdown-item>
                <el-dropdown-item command="0" :class="{ active: queryParams.status === '0' }">待审核</el-dropdown-item>
                <el-dropdown-item command="1" :class="{ active: queryParams.status === '1' }">已通过</el-dropdown-item>
                <el-dropdown-item command="2" :class="{ active: queryParams.status === '2' }">已驳回</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <!-- Status Summary Chips -->
        <div class="status-chips">
           <span class="chip" :class="{ active: queryParams.status === '' }" @click="handleStatusFilter('')">全部</span>
           <span class="chip warning" :class="{ active: queryParams.status === '0' }" @click="handleStatusFilter('0')">待审</span>
           <span class="chip success" :class="{ active: queryParams.status === '1' }" @click="handleStatusFilter('1')">通过</span>
           <span class="chip danger" :class="{ active: queryParams.status === '2' }" @click="handleStatusFilter('2')">驳回</span>
        </div>
      </div>

      <!-- Sidebar List -->
      <div class="sidebar-content" v-loading="loading">
        <el-scrollbar>
          <div v-if="filteredList.length === 0" class="empty-list">
            <el-empty description="暂无符合条件的证书" :image-size="80" />
          </div>
          <transition-group name="list-anim" tag="div">
            <div 
              v-for="(item, index) in filteredList" 
              :key="item.id"
              class="list-item"
              :class="{ active: currentId === item.id }"
              @click="handleSelect(item)"
            >
              <div class="item-status-strip" :class="getStatusClass(item.status)"></div>
              <div class="item-main">
                <div class="item-header">
                   <span class="student-name">{{ item.studentName }}</span>
                   <span class="time-ago">{{ formatTime(item.uploadTime) }}</span>
                </div>
                <div class="cert-name">{{ item.certName }}</div>
                <div class="item-footer">
                  <span class="class-name">{{ item.className }}</span>
                  <el-tag size="small" :type="getStatusType(item.status)" effect="plain" round class="status-tag">
                     {{ getStatusText(item.status) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </transition-group>
        </el-scrollbar>
      </div>
    </aside>

    <!-- Right Canvas: The Detail -->
    <main class="detail-canvas">
      <!-- Key is used to force re-render transition when ID changes -->
      <transition name="fade-slide" mode="out-in">
        <div v-if="currentCert" :key="currentCert.id" class="detail-wrapper">
          <CertificateCard 
            :data="currentCert" 
            @approve="handleApprove" 
            @reject="handleReject"
          />
        </div>
        <div v-else class="empty-state-canvas" :key="'empty'">
          <div class="empty-content">
            <img src="https://cdni.iconscout.com/illustration/premium/thumb/selecting-file-illustration-download-in-svg-png-gif-file-formats--select-document-folder-business-miscellaneous-pack-illustrations-5231718.png?f=webp" alt="Select" class="empty-img"/>
            <h3>准备好开始工作了</h3>
            <p>从左侧列表中选择一个项目开始审核</p>
          </div>
        </div>
      </transition>
    </main>

    <!-- 驳回弹窗 (Reused Logic) -->
    <el-dialog v-model="rejectDialogVisible" title="驳回审核" width="400px" class="glass-dialog">
      <el-form :model="rejectForm">
        <el-form-item>
          <el-input 
            v-model="rejectForm.reason" 
            type="textarea" 
            placeholder="请输入驳回原因..." 
            :rows="4"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="rejectDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmReject">确认驳回</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { getCertificates, updateStatus } from '@/api/mock/certificate'
import { ElMessage } from 'element-plus'
import { Search, Filter } from '@element-plus/icons-vue'
import CertificateCard from './components/CertificateCard.vue'

// State
const loading = ref(false)
const tableData = ref([])
const searchText = ref('')
const queryParams = reactive({
  status: '' // Default filter
})

const currentId = ref(null)

// Derived State
const filteredList = computed(() => {
  let list = tableData.value;
  // 1. Filter by Text
  if (searchText.value) {
    list = list.filter(item => 
      item.studentName.includes(searchText.value) || 
      item.certName.includes(searchText.value)
    );
  }
  // 2. Filter by Status
  if (queryParams.status !== '') {
    // Note: status from select/mock might be string or number, force string comparison
    list = list.filter(item => String(item.status) === String(queryParams.status));
  }
  return list;
})

const currentCert = computed(() => {
  // Find in the FULL tableData to ensure we can show it even if it momentarily disappears from filter
  // But for better UX, usually we want to confirm it exists
  return tableData.value.find(item => item.id === currentId.value) || null
})

// Reject Dialog
const rejectDialogVisible = ref(false)
const rejectForm = reactive({
  id: null,
  reason: ''
})

// Lifecycle
onMounted(() => {
  getList()
})

// Methods
const getList = async () => {
  loading.value = true
  try {
    const res = await getCertificates({}) // Fetch ALL data, handle filtering locally for smoothness
    tableData.value = res.data.list
    autoSelectFirst()
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const autoSelectFirst = () => {
  if (filteredList.value.length > 0 && !currentId.value) {
    currentId.value = filteredList.value[0].id
  }
}

const handleStatusFilter = (command) => {
  queryParams.status = command
  // Clear selection if current item is filtered out? 
  // Or keep it? keeping it is better usually, but if we filter strictly:
  nextTick(() => {
    if (filteredList.value.length > 0) {
       // if current item is NOT in filtered list, select the first one
       const exists = filteredList.value.find(item => item.id === currentId.value)
       if (!exists) {
         currentId.value = filteredList.value[0].id
       }
    } else {
       currentId.value = null
    }
  })
}

const handleSelect = (item) => {
  currentId.value = item.id
}

// *** Auto-Advance Logic ***
const advanceToNext = (processedId) => {
  // 1. Find the index where the processed item WAS
  // Since filters are computed, if we change the status, the item might be removed from filteredList instantly
  // So we need to find the "Next" candidate.
  
  // If we assume the item IS STILL visible (e.g. "All" filter), we just stay or move next?
  // If we filter "Pending", item status changes to "Success", it disappears.
  
  // The 'filteredList' will update automatically.
  // We just need to check if currentId is still valid in filteredList
  
  nextTick(() => {
    const stillExists = filteredList.value.find(item => item.id === currentId.value)
    if (!stillExists) {
       // Item disappeared (good, it was processed).
       // Select the FIRST item in the new filtered list (which was previously the second item, or the one that shifted up)
       if (filteredList.value.length > 0) {
         // Silky transition: Select the new top item (or the one at previous index if we want to be fancy)
         // Simple strategy: Select first available.
         currentId.value = filteredList.value[0].id
       } else {
         currentId.value = null
       }
    } else {
      // Item still exists (e.g. "All" filter).
      // Maybe user wants to stay on it to see the result, OR move next.
      // User said: "Next card smoothly switches up".
      // Let's find current index and move +1
      const idx = filteredList.value.findIndex(item => item.id === currentId.value)
      if (idx !== -1 && idx < filteredList.value.length - 1) {
         currentId.value = filteredList.value[idx + 1].id
      }
    }
  })
}

// Helpers
const getStatusType = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger' }
  return map[status]
}
const getStatusText = (status) => {
  const map = { 0: '待审核', 1: '已通过', 2: '已驳回' }
  return map[status]
}
const getStatusClass = (status) => {
   const map = { 0: 'bg-warning', 1: 'bg-success', 2: 'bg-danger' }
   return map[status]
}
const formatTime = (timeStr) => {
  return timeStr ? timeStr.split(' ')[0] : ''
}

// Actions
const handleApprove = (row) => {
  // Optimistic UI update
  const target = tableData.value.find(i => i.id === row.id)
  if (target) {
     target.status = 1 // Update Status
     ElMessage.success('审核已通过，自动切换下一条')
     
     // Trigger Auto Advance
     advanceToNext(row.id)
     
     // Call API in background
     updateStatus(row.id, 1).catch(() => {
        target.status = 0 // Revert
        ElMessage.error('操作失败，已撤回')
     })
  }
}

const handleReject = (row) => {
  rejectForm.id = row.id
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectForm.reason) return ElMessage.warning('请输入原因')
  
  const target = tableData.value.find(i => i.id === rejectForm.id)
  if (target) {
    target.status = 2
    target.rejectReason = rejectForm.reason
    ElMessage.success('已驳回，自动切换下一条')
    
    rejectDialogVisible.value = false
    advanceToNext(target.id)
    
     // Call API in background
     updateStatus(rejectForm.id, 2, rejectForm.reason).catch(() => {
        target.status = 0 // Revert
        ElMessage.error('操作失败，已撤回')
     })
  }
}
</script>

<style scoped lang="scss">
// Tokens
$bg-sidebar: #ffffff;
$bg-canvas: #F5F7FA;
$primary: #409EFF;
$border: #EBEEF5;
$text-main: #303133;
$text-sub: #909399;
$active-bg: #ecf5ff;

.workbench-container {
  display: flex;
  height: calc(100vh - 84px); 
  background-color: $bg-canvas;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

// 1. Sidebar Panel
.sidebar-panel {
  width: 380px;
  background: $bg-sidebar;
  border-right: 1px solid $border;
  display: flex;
  flex-direction: column;
  z-index: 10;
  box-shadow: 4px 0 24px rgba(0,0,0,0.02);
  
  .sidebar-header {
    padding: 24px;
    border-bottom: 1px solid $border;
    
    .sidebar-title {
      margin: 0 0 16px 0;
      font-size: 20px;
      font-weight: 700;
      color: $text-main;
      letter-spacing: -0.5px;
    }
    
    .filter-group {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      
      .modern-search {
        flex: 1;
        :deep(.el-input__wrapper) {
          border-radius: 8px;
          background-color: #f5f7fa;
          box-shadow: none !important;
          padding: 8px 12px;
          &:hover, &.is-focus { background-color: white; box-shadow: 0 0 0 1px $primary !important; }
        }
      }
      
      .filter-btn {
        width: 40px; 
        height: 40px;
        border-color: transparent;
        background: #f5f7fa;
        &:hover { color: $primary; background: #ecf5ff; }
      }
    }
    
    .status-chips {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;
      scrollbar-width: none;
      
      .chip {
        font-size: 13px;
        padding: 5px 14px;
        border-radius: 100px;
        background: #f5f7fa;
        color: $text-sub;
        cursor: pointer;
        white-space: nowrap;
        font-weight: 500;
        transition: all 0.2s;
        
        &:hover { background: #e6e8eb; }
        &.active { background: #333; color: white; transform: translateY(-1px); }
        
        // Contextual colors for active states
        &.warning.active { background: #fa8c16; }
        &.success.active { background: #52c41a; }
        &.danger.active { background: #F56C6C; }
      }
    }
  }
  
  .sidebar-content {
    flex: 1;
    overflow: hidden;
    position: relative;
    
    .list-item {
      padding: 20px 24px;
      border-bottom: 1px solid #f9fafc;
      cursor: pointer;
      position: relative;
      transition: all 0.2s;
      background: white;
      
      &:hover {
        background-color: #fcfcfd;
        padding-left: 28px; // Subtle shift
      }
      
      &.active {
        background-color: $active-bg;
        
        .item-status-strip {
          transform: scaleY(1);
        }
        .student-name { color: $primary; }
      }
      
      .item-status-strip {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        transform: scaleY(0);
        transition: transform 0.2s cubic-bezier(0.2, 0, 0, 1);
        
        &.bg-warning { background-color: #fa8c16; }
        &.bg-success { background-color: #52c41a; }
        &.bg-danger { background-color: #F56C6C; }
      }
      
      .item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .student-name {
          font-weight: 700;
          color: $text-main;
          font-size: 15px;
        }
        .time-ago {
          font-size: 12px;
          color: #c0c4cc;
        }
      }
      
      .cert-name {
        font-size: 14px;
        color: $text-sub;
        margin-bottom: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .item-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .class-name {
          font-size: 12px;
          color: #909399;
          background: #f5f7fa;
          padding: 3px 8px;
          border-radius: 6px;
        }
        
        .status-tag {
          border-color: transparent;
        }
      }
    }
  }
}

// 2. Main Canvas
.detail-canvas {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  overflow: hidden; // Prevent double scrollbars
  position: relative;
  
  .detail-wrapper {
    width: 100%;
    max-width: 1000px;
    height: 100%;
    max-height: 800px;
  }
}

// 3. Empty State
.empty-state-canvas {
  text-align: center;
  color: $text-sub;
  
  .empty-img {
    width: 240px;
    margin-bottom: 32px;
    opacity: 0.9;
  }
  
  h3 {
    font-size: 20px;
    color: $text-main;
    margin-bottom: 12px;
  }
}

// 4. Animations
/* List Animation - Staggered or Grouped */
.list-anim-enter-active,
.list-anim-leave-active {
  transition: all 0.3s ease;
}
.list-anim-enter-from,
.list-anim-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
.list-anim-leave-active {
  position: absolute; // Remove from flow smoothly
  width: 100%; 
}

/* Detail Panel Transition - Fade and slightly Slide Up */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.98);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.98);
}

</style>
