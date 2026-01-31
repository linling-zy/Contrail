<template>
  <div class="student-workbench">
    <!-- Sidebar: Student List -->
    <aside class="sidebar-panel">
      <!-- 1. Formal Toolbar Header -->
      <div class="sidebar-toolbar">
         <div class="back-link" @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回上一级
         </div>
         <div class="class-info">
            <h2 class="class-title">{{ className || '班级管理' }}</h2>
            <span class="count-badge">共 {{ filteredList.length }} 人</span>
         </div>
      </div>

      <!-- 2. Search & Actions Area -->
      <div class="sidebar-actions">
        <el-input 
          v-model="queryParams.name" 
          placeholder="搜索姓名或学号..." 
          prefix-icon="Search"
          clearable
          class="formal-search"
          @input="handleSearch"
        />
        
        <div class="action-buttons">
           <el-button type="primary" plain class="action-btn" @click="handleImport">
              <el-icon><Upload /></el-icon> 导入数据
           </el-button>
           <el-button type="success" plain class="action-btn" @click="handleExport">
              <el-icon><Download /></el-icon> 导出报表
           </el-button>
        </div>
      </div>

      <!-- 3. Enterprise List -->
      <div class="sidebar-content" v-loading="loading">
         <div class="list-header-row">
            <span class="col-name">姓名</span>
            <span class="col-id">学号</span>
            <span class="col-status">状态</span>
         </div>
         <el-scrollbar ref="scrollbarRef">
            <div v-if="filteredList.length === 0" class="empty-list">
               <el-empty description="暂无数据" :image-size="60" />
            </div>
            
            <div 
              v-for="student in filteredList" 
              :key="student.id"
              :ref="(el) => setItemRef(el, student.id)"
              class="student-row"
              :class="{ active: currentId === student.id }"
              @click="handleSelect(student)"
            >
              <div class="cell-name">
                 <el-avatar :size="24" class="mini-avatar" shape="square">{{ student.name.charAt(0) }}</el-avatar>
                 <span class="text">{{ student.name }}</span>
              </div>
              <div class="cell-id">{{ student.studentNo }}</div>
              <div class="cell-status">
                 <el-tag v-if="isQualified(student)" type="success" size="small" effect="plain">合格</el-tag>
                 <span v-else class="text-gray">-</span>
              </div>
            </div>
         </el-scrollbar>
      </div>
    </aside>

    <!-- Main Canvas: Detail View -->
    <main class="detail-canvas" @wheel="handleWheel">
      <transition name="fade-quick" mode="out-in">
         <div v-if="currentStudent" :key="currentStudent.id" ref="detailContentRef" class="canvas-wrapper">
            <StudentArchive 
               :studentData="currentStudent" 
               @saved="handleCardSaved"
               @cancel="() => {}" 
            />
         </div>
         <div v-else class="empty-canvas">
             <div class="empty-state-box">
                <el-icon class="empty-icon"><User /></el-icon>
                <h3>请选择学生</h3>
                <p>在左侧列表中选择一名学生以查看详细档案</p>
             </div>
         </div>
      </transition>
    </main>

    <!-- 批量导出弹窗 -->
    <el-dialog v-model="exportDialogVisible" title="导出数据" width="400px" class="formal-dialog">
      <div class="export-content">
        <div v-if="exportStatus === 'processing'">
           <el-progress :percentage="exportProgress" status="success" />
           <div class="status-text">正在生成报表...</div>
        </div>
        <div v-else-if="exportStatus === 'completed'" class="completed-state">
           <el-result icon="success" title="导出成功" sub-title="数据已准备就绪">
             <template #extra>
               <el-button type="primary" @click="handleDownload">立即下载</el-button>
             </template>
           </el-result>
        </div>
        <div v-else-if="exportStatus === 'failed'" class="failed-state">
           <el-result icon="error" title="导出失败" sub-title="系统繁忙，请稍后重试">
           </el-result>
        </div>
      </div>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入数据" width="500px" class="formal-dialog">
      <div class="upload-container">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          action="#"
          accept=".xlsx, .xls"
          :http-request="customUploadRequest"
          :show-file-list="false"
          :disabled="importLoading"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 Excel 文件拖拽至此，或 <em>点击上传</em>
          </div>
          <template #tip>
             <div class="el-upload__tip">支持 .xlsx / .xls 格式文件</div>
          </template>
        </el-upload>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getStudents, startExportTask, getExportTaskStatus, uploadStudentFile } from '@/api/mock/student'
import { getDepartments } from '@/api/mock/system'
import { ElMessage } from 'element-plus'
import { Search, ArrowLeft, Upload, Download, User, UploadFilled } from '@element-plus/icons-vue'
import StudentArchive from './components/StudentArchive.vue'

const router = useRouter()
const route = useRoute()

// Data
const loading = ref(false)
const tableData = ref([])
const className = ref('')
const queryParams = reactive({
  name: '',
  classId: route.params.classId
})

const currentId = ref(null)

// Computed
const filteredList = computed(() => {
   if (!queryParams.name) return tableData.value
   const lower = queryParams.name.toLowerCase()
   return tableData.value.filter(s => 
     s.name.includes(lower) || 
     String(s.studentNo).includes(lower)
   )
})

const currentStudent = computed(() => {
   return tableData.value.find(s => s.id === currentId.value) || null
})

// Export/Import State
const exportDialogVisible = ref(false)
const exportStatus = ref('processing')
const exportProgress = ref(0)
const exportTaskId = ref(null)
const downloadUrl = ref('')
let exportTimer = null

const importDialogVisible = ref(false)
const importLoading = ref(false)
const uploadRef = ref(null)

// Navigation Logic
const detailContentRef = ref(null)
const lastWheelTime = ref(0)
const WHEEL_THROTTLE = 500 // ms

// Lifecycle
onMounted(() => {
  getClassName()
  getList()
})

// Methods
const getList = async () => {
  loading.value = true
  try {
    const res = await getStudents({ classId: queryParams.classId }) 
    tableData.value = res.data.list
    if (tableData.value.length > 0 && !currentId.value) {
       currentId.value = tableData.value[0].id
    }
  } catch (error) {
    ElMessage.error('无法加载学生数据')
  } finally {
    loading.value = false
  }
}

const getClassName = async () => {
    try {
        const res = await getDepartments()
        const cls = res.data.find(d => d.id == route.params.classId)
        if(cls) className.value = cls.name
    } catch (e) {}
}

const handleSearch = () => {
   // Client-side filtering
}

const handleSelect = (student) => {
   currentId.value = student.id
}

const switchStudent = (direction) => { // 1 for next, -1 for prev
   if (filteredList.value.length <= 1) return
   
   const currentIndex = filteredList.value.findIndex(s => s.id === currentId.value)
   if (currentIndex === -1) return

   let nextIndex = currentIndex + direction
   
   // Bound checks
   if (nextIndex < 0) {
      if (currentIndex === 0) {
         ElMessage.info('已经是第一个学生了')
         return 
      }
      nextIndex = 0
   }
   if (nextIndex >= filteredList.value.length) {
      if (currentIndex === filteredList.value.length - 1) {
         ElMessage.info('已经是最后一个学生了')
         return
      }
      nextIndex = filteredList.value.length - 1
   }

   const nextStudent = filteredList.value[nextIndex]
   currentId.value = nextStudent.id
}

const scrollbarRef = ref(null)
const itemRefs = ref({})

const setItemRef = (el, id) => {
   if (el) itemRefs.value[id] = el
}

import { nextTick, watch } from 'vue'

watch(currentId, async (newId) => {
   if (!newId) return
   await nextTick()
   const el = itemRefs.value[newId]
   if (el && scrollbarRef.value) {
      // Manual scroll calculation
      // el-scrollbar exposes setScrollTop or wrapRef usually
      // We can use scrollIntoView on the element if the container is the scroll parent.
      // Element Plus scrollbar wrap is the scroll parent.
      
      const wrap = scrollbarRef.value.wrapRef
      if (wrap) {
         const top = el.offsetTop
         const height = el.clientHeight
         const containerHeight = wrap.clientHeight
         
         // Center it
         let targetScroll = top - containerHeight / 2 + height / 2
         wrap.scrollTo({ top: targetScroll, behavior: 'smooth' })
      } else {
          // Fallback if direct scrollIntoView is supported and easier
          el.scrollIntoView({ block: 'center', behavior: 'smooth' })
      }
   }
})

const handleWheel = (e) => {
   // ... existing code ...
   const now = Date.now()
   if (now - lastWheelTime.value < WHEEL_THROTTLE) return

   const delta = e.deltaY
   const wrapper = detailContentRef.value 
   // Note: detailContentRef is the specific content div.
   // But the scrolling usually happens on the PARENT container (.detail-canvas).
   // Let's check where the scroll target is.
   
   const container = document.querySelector('.detail-canvas')
   if (!container) return

   // Check if content is scrollable
   // scrollHeight > clientHeight
   const isScrollable = container.scrollHeight > container.clientHeight
   
   if (!isScrollable) {
      // Not scrollable, just switch
      if (Math.abs(delta) > 20) { // Threshold
         switchStudent(delta > 0 ? 1 : -1)
         lastWheelTime.value = now
      }
   } else {
      // Scrollable
      const isAtTop = container.scrollTop <= 10
      const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 10
      
      if (delta < 0 && isAtTop) {
         // Scrolling UP at TOP -> Prev
         switchStudent(-1)
         lastWheelTime.value = now
      } else if (delta > 0 && isAtBottom) {
         // Scrolling DOWN at BOTTOM -> Next
         switchStudent(1)
         lastWheelTime.value = now
      }
   }
}

const isQualified = (student) => {
   return student.status && student.status.admission === 'qualified'
}

const handleCardSaved = () => {
   getList()
}

const goBack = () => {
  router.push('/students')
}

// --- Import/Export Logic ---
const handleExport = async () => {
    if (!queryParams.classId) return
    try {
        const res = await startExportTask(queryParams.classId)
        exportTaskId.value = res.data.taskId
        exportDialogVisible.value = true
        exportStatus.value = 'processing'
        exportProgress.value = 0
        pollExportStatus()
    } catch (error) {
        ElMessage.error('导出失败')
    }
}

const pollExportStatus = () => {
    if (exportTimer) clearInterval(exportTimer)
    exportTimer = setInterval(async () => {
        try {
            const res = await getExportTaskStatus(exportTaskId.value)
            const { status, progress, download_url } = res.data
            exportStatus.value = status
            exportProgress.value = progress
            if (status === 'completed') {
                clearInterval(exportTimer)
                downloadUrl.value = download_url
            } else if (status === 'failed') {
                clearInterval(exportTimer)
            }
        } catch (error) {
            clearInterval(exportTimer)
            exportStatus.value = 'failed'
        }
    }, 1000)
}

const handleDownload = () => {
    ElMessage.success('下载开始: ' + downloadUrl.value)
    exportDialogVisible.value = false
}

const handleImport = () => {
  importDialogVisible.value = true
}

const customUploadRequest = async (option) => {
  const formData = new FormData()
  formData.append('file', option.file)
  importLoading.value = true
  try {
    const res = await uploadStudentFile(formData)
    ElMessage.success(`导入完成: 成功${res.data.successCount}, 失败${res.data.failCount}`)
    importDialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('导入出错')
  } finally {
    importLoading.value = false
  }
}
</script>

<style scoped lang="scss">
$sidebar-width: 320px;
$bg-sidebar: #f8f9fa;
$bg-canvas: #ffffff;
$border-color: #dcdfe6;
$text-primary: #303133;
$text-secondary: #909399;
$primary-color: #409EFF;

.student-workbench {
  display: flex;
  height: 100%;
  background-color: $bg-canvas;
  overflow: hidden;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

// Sidebar
.sidebar-panel {
  width: $sidebar-width;
  background: #ffffff;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  z-index: 10;

  .sidebar-toolbar {
     padding: 16px 20px;
     border-bottom: 1px solid $border-color;
     background: #fcfcfc;
     
     .back-link {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 14px;
        color: $text-secondary;
        cursor: pointer;
        margin-bottom: 12px;
        &:hover { color: $primary-color; }
     }
     
     .class-info {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        
        .class-title {
           margin: 0;
           font-size: 18px;
           font-weight: 600;
           color: $text-primary;
        }
        .count-badge {
           font-size: 12px;
           color: $text-secondary;
        }
     }
  }

  .sidebar-actions {
     padding: 16px 20px;
     border-bottom: 1px solid $border-color;
     display: flex;
     flex-direction: column;
     gap: 12px;
     
     .formal-search {
        :deep(.el-input__wrapper) {
           box-shadow: 0 0 0 1px $border-color inset;
           &:hover { box-shadow: 0 0 0 1px $text-secondary inset; }
           &.is-focus { box-shadow: 0 0 0 1px $primary-color inset !important; }
        }
     }
     
     .action-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        
        .action-btn {
           width: 100%;
           justify-content: center;
           margin: 0;
        }
     }
  }

  .sidebar-content {
     flex: 1;
     display: flex;
     flex-direction: column;
     background: #ffffff;
     overflow: hidden;
     
     :deep(.el-scrollbar) {
        flex: 1;
     }
     
     .list-header-row {
        display: flex;
        padding: 8px 16px;
        background: #f5f7fa;
        border-bottom: 1px solid $border-color;
        font-size: 12px;
        color: $text-secondary;
        font-weight: 600;
        
        .col-name { flex: 2; }
        .col-id { flex: 2; }
        .col-status { flex: 1; text-align: right; }
     }
     
     .student-row {
        display: flex;
        padding: 12px 16px;
        border-bottom: 1px solid #f2f2f5;
        cursor: pointer;
        transition: background 0.1s;
        align-items: center;
        
        &:hover { background: #f5f7fa; }
        &.active { 
           background: #ecf5ff; 
           border-left: 3px solid $primary-color;
           padding-left: 13px; // Adjust for border
        }
        
        .cell-name {
           flex: 2;
           display: flex;
           align-items: center;
           gap: 8px;
           .mini-avatar { background: #c0c4cc; }
           .text { font-size: 14px; font-weight: 500; color: $text-primary; }
           
           /* Active overrides */
           // .active & .mini-avatar { background: $primary-color; }
        }
        
        .cell-id {
           flex: 2;
           font-size: 13px;
           color: $text-secondary;
           font-family: monospace;
        }
        
        .cell-status {
           flex: 1;
           text-align: right;
           font-size: 12px;
           .text-gray { color: #dcdfe6; }
        }
     }
  }
}

// Canvas
.detail-canvas {
   flex: 1;
   background: #f2f3f5;
   padding: 24px;
   display: flex;
   justify-content: center;
   overflow-y: auto;
   
   .canvas-wrapper {
      width: 100%;
      max-width: 1000px;
   }
}

.empty-canvas {
   display: flex;
   height: 100%;
   align-items: center;
   justify-content: center;
   color: $text-secondary;
   
   .empty-state-box {
      text-align: center;
      .empty-icon { font-size: 48px; margin-bottom: 16px; color: #dcdfe6; }
      h3 { margin: 0 0 8px 0; color: $text-primary; }
   }
}

// Dialog
:deep(.formal-dialog) {
   border-radius: 4px;
   .el-dialog__header {
      border-bottom: 1px solid $border-color;
      padding: 16px 20px;
      margin: 0;
   }
   .el-dialog__body {
      padding: 24px;
   }
}

// Transitions
.fade-quick-enter-active, .fade-quick-leave-active { transition: opacity 0.2s; }
.fade-quick-enter-from, .fade-quick-leave-to { opacity: 0; }
</style>
