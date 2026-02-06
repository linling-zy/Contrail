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
        <div v-if="className" class="import-info" style="margin-bottom: 16px; padding: 12px; background: var(--el-bg-color-page); border-radius: 4px;">
          <el-text type="info">将导入到班级：<strong>{{ className }}</strong></el-text>
        </div>
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
             <div class="el-upload__tip">
               <div>支持 .xlsx / .xls 格式文件</div>
               <div style="margin-top: 4px; color: var(--el-text-color-secondary);">
                 Excel 表格需包含列：学号、姓名、身份证号（不需要班级名称列）
               </div>
             </div>
          </template>
        </el-upload>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getStudents, getStudentDetail, importStudents, startExportTask, getExportTaskStatus, downloadExportFile } from '@/api/student'
import { getDepartments } from '@/api/system'
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
  classId: route.params.classId || null,
  department_id: route.params.classId || null  // 使用 department_id 作为主要参数
})

const currentId = ref(null)
// 已加载详情的学生ID列表，避免重复请求
const loadedDetailIds = ref([])

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

// 加载单个学生的详细信息（评语 + 证书等）
const loadStudentDetail = async (studentId) => {
  if (!studentId) return
  // 已经加载过则直接跳过
  if (loadedDetailIds.value.includes(studentId)) return

  try {
    const res = await getStudentDetail(studentId)
    // 适配后端返回的数据结构
    const detail = res.student || (res.data && res.data.student) || null
    if (!detail) return

    const comments = res.comments || (res.data && res.data.comments) || []
    const certificates = res.certificates || (res.data && res.data.certificates) || []

    // 教师评价：使用最新一条评语的内容
    let teacherEvaluation = ''
    if (Array.isArray(comments) && comments.length > 0) {
      teacherEvaluation = comments[0].content || ''
    }

    // 证书列表：适配到前端表格需要的字段
    const mappedCertificates = Array.isArray(certificates)
      ? certificates.map((c) => {
          const statusCode = typeof c.status === 'number' ? c.status : null
          return {
            name: c.name || c.certName || '',
            date: (c.upload_time || c.create_time || '').split('T')[0] || '',
            // 后端状态：0待审/1通过/2驳回，这里简单映射为“已获得/审核中”
            status: statusCode === 1 ? 'obtained' : 'pending',
            rawStatus: c.status,
            imgUrl: c.imgUrl || c.image_url || ''
          }
        })
      : []

    // 找到并更新列表中的对应学生记录
    const idx = tableData.value.findIndex((s) => s.id === studentId)
    if (idx !== -1) {
      tableData.value[idx] = {
        ...tableData.value[idx],
        // 覆盖/补充档案字段
        credits: detail.credits ?? tableData.value[idx].credits ?? null,
        gpa: detail.gpa ?? tableData.value[idx].gpa ?? null,
        birthplace: detail.birthplace || tableData.value[idx].birthplace || '',
        ethnicity: detail.ethnicity || tableData.value[idx].ethnicity || '',
        politicalAffiliation:
          detail.political_affiliation ||
          tableData.value[idx].politicalAffiliation ||
          '',
        phone: detail.phone || tableData.value[idx].phone || '',
        // 教师评价与证书列表
        teacherEvaluation,
        certificates: mappedCertificates
      }
    }

    loadedDetailIds.value.push(studentId)
  } catch (error) {
    // 静默失败，只在控制台打印，避免打扰操作
    console.error('加载学生详情失败:', error)
  }
}

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

// 监听路由参数变化（部门选择变化）
watch(() => route.params.classId, (newClassId) => {
  if (newClassId) {
    queryParams.classId = newClassId
    queryParams.department_id = newClassId
    getClassName()
    getList()
  }
}, { immediate: false })

// Methods
const getList = async () => {
  loading.value = true
  try {
    // 使用 department_id 参数调用真实 API
    const params = {}
    if (queryParams.department_id) {
      params.department_id = queryParams.department_id
    }
    // 如果有搜索关键词，也传递
    if (queryParams.name) {
      params.filter = 'name'
      params.keyword = queryParams.name
    }
    
    const res = await getStudents(params)
    
    // 适配后端返回的数据格式：{ total, page, per_page, pages, items }
    if (res.items) {
      // 后端返回格式
      tableData.value = res.items.map(item => {
        // 转换数据格式以适配前端显示
        const mapped = {
          id: item.id,
          name: item.name,
          studentNo: item.student_id || item.id_card_no, // 使用 student_id 或 id_card_no
          idCard: item.id_card_no || '', // 添加身份证号字段映射
          className: item.class_name || '',
          totalScore: item.total_score || 0,
          status: item.process_status || {
            preliminary: item.preliminary_status || 'pending',
            medical: item.medical_status || 'pending',
            political: item.political_status || 'pending',
            admission: item.admission_status || 'pending'
          },
          // 新增：将后端返回的扩展字段一并挂到列表项上，供详情组件使用
          credits: item.credits ?? null,
          gpa: item.gpa ?? null,
          birthplace: item.birthplace || '',
          ethnicity: item.ethnicity || '',
          politicalAffiliation: item.political_affiliation || '',
          phone: item.phone || ''
        }
        
        return mapped
      })
    } else if (res.data && res.data.list) {
      // Mock 数据格式（兼容）
      tableData.value = res.data.list
    } else {
      tableData.value = []
    }
    
    if (tableData.value.length > 0 && !currentId.value) {
       currentId.value = tableData.value[0].id
    }
  } catch (error) {
    console.error('加载学生数据失败:', error)
    ElMessage.error(error.message || '无法加载学生数据')
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const getClassName = async () => {
    try {
        const res = await getDepartments({ per_page: 100 })
        
        // 适配后端返回的数据格式
        let deptList = []
        if (res.items) {
            deptList = res.items
        } else if (res.data && Array.isArray(res.data)) {
            deptList = res.data
        }
        
        const cls = deptList.find(d => d.id == route.params.classId)
        if (cls) {
            // 构建部门名称
            className.value = cls.class_name || 
                            `${cls.college || ''}${cls.grade || ''}${cls.major || ''}${cls.class_name || ''}`.trim() || 
                            '未知班级'
        }
    } catch (e) {
        console.error('获取班级名称失败:', e)
    }
}

const handleSearch = () => {
   // 触发重新获取数据（带搜索关键词）
   getList()
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

watch(currentId, async (newId) => {
   if (!newId) return

   // 当切换选中学生时，按需加载其详细档案（评语 + 证书）
   loadStudentDetail(newId)

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
        
        // 适配后端返回的数据格式：{ code: 200, task_id: "..." }
        if (res.code === 200 && res.task_id) {
            exportTaskId.value = res.task_id
            exportDialogVisible.value = true
            exportStatus.value = 'processing'
            exportProgress.value = 0
            pollExportStatus()
        } else if (res.task_id) {
            // 兼容其他格式
            exportTaskId.value = res.task_id
            exportDialogVisible.value = true
            exportStatus.value = 'processing'
            exportProgress.value = 0
            pollExportStatus()
        } else {
            ElMessage.error(res.error || '导出任务创建失败')
        }
    } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error(error.message || '导出失败')
    }
}

const pollExportStatus = () => {
    if (exportTimer) clearInterval(exportTimer)
    exportTimer = setInterval(async () => {
        try {
            const res = await getExportTaskStatus(exportTaskId.value)
            
            // 适配后端返回的数据格式：{ code: 200, status, progress, total, download_url, error }
            if (res.code === 200) {
                const { status, progress, total, download_url, error } = res
                exportStatus.value = status
                exportProgress.value = total > 0 ? Math.round((progress / total) * 100) : 0
                
                if (status === 'completed') {
                    clearInterval(exportTimer)
                    if (download_url) {
                        // 使用完整URL或相对路径
                        downloadUrl.value = download_url.startsWith('http') 
                            ? download_url 
                            : `http://127.0.0.1:5000${download_url}`
                    }
                } else if (status === 'failed') {
                    clearInterval(exportTimer)
                    if (error) {
                        ElMessage.error(`导出失败: ${error}`)
                    }
                }
            } else {
                // 兼容其他格式
                const { status, progress, download_url } = res.data || res
                exportStatus.value = status
                exportProgress.value = progress || 0
                if (status === 'completed') {
                    clearInterval(exportTimer)
                    downloadUrl.value = download_url
                } else if (status === 'failed') {
                    clearInterval(exportTimer)
                }
            }
        } catch (error) {
            console.error('查询导出状态失败:', error)
            clearInterval(exportTimer)
            exportStatus.value = 'failed'
            ElMessage.error(error.message || '查询导出状态失败')
        }
    }, 1000)
}

const handleDownload = async () => {
    if (exportTaskId.value) {
        // 始终使用 downloadExportFile API（可以添加 Authorization 头）
        try {
            const blob = await downloadExportFile(exportTaskId.value)
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `学生档案导出_${new Date().getTime()}.zip`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)
            ElMessage.success('下载完成')
        } catch (error) {
            console.error('下载失败:', error)
            ElMessage.error(error.message || '下载失败')
        }
    }
    exportDialogVisible.value = false
}

const handleImport = () => {
  importDialogVisible.value = true
}

const customUploadRequest = async (option) => {
  const formData = new FormData()
  formData.append('file', option.file)
  
  // 获取当前班级的 department_id
  const currentDepartmentId = queryParams.department_id || queryParams.classId
  if (!currentDepartmentId) {
    ElMessage.error('请先选择班级')
    importLoading.value = false
    return
  }
  
  importLoading.value = true
  try {
    const res = await importStudents(formData, currentDepartmentId)
    
    if (res.code === 200 && res.data) {
      const { success_count, skip_count, error_count, errors } = res.data
      
      // 构建提示消息
      let message = `导入完成: 成功 ${success_count} 条`
      if (skip_count > 0) {
        message += `，跳过 ${skip_count} 条`
      }
      if (error_count > 0) {
        message += `，失败 ${error_count} 条`
      }
      
      if (success_count > 0) {
        ElMessage.success(message)
      } else if (error_count > 0 || skip_count > 0) {
        ElMessage.warning(message)
      } else {
        ElMessage.info('没有数据被导入')
      }
      
      // 如果有错误详情，在控制台输出
      if (errors && errors.length > 0) {
        console.warn('导入错误详情:', errors)
        // 可以选择显示错误详情，但为了避免信息过多，只在控制台输出
        if (errors.length <= 10) {
          const errorMsg = errors.map(e => `第${e.row}行: ${e.error}`).join('\n')
          ElMessage.warning(`部分数据导入失败:\n${errorMsg}`)
        }
      }
      
      importDialogVisible.value = false
      // 刷新列表
      getList()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (error) {
    console.error('导入出错:', error)
    ElMessage.error(error.message || '导入出错，请检查文件格式')
  } finally {
    importLoading.value = false
  }
}
</script>

<style scoped lang="scss">
$sidebar-width: 320px;
$bg-sidebar: var(--el-bg-color-page);
$bg-canvas: var(--el-bg-color);
$border-color: var(--el-border-color-light);
$text-primary: var(--el-text-color-primary);
$text-secondary: var(--el-text-color-secondary);
$primary-color: var(--el-color-primary);

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
  background: var(--el-bg-color);
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  z-index: 10;

  .sidebar-toolbar {
     padding: 16px 20px;
     border-bottom: 1px solid $border-color;
     background: var(--el-bg-color);
     
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
     background: var(--el-bg-color);
     overflow: hidden;
     
     :deep(.el-scrollbar) {
        flex: 1;
     }
     
     .list-header-row {
        display: flex;
        padding: 8px 16px;
        background: var(--el-fill-color-light);
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
        
        &:hover { background: var(--el-fill-color-light); }
        &.active { 
           background: var(--el-color-primary-light-9); 
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
   background: var(--el-bg-color-page);
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
