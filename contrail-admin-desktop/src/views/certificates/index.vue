<template>
  <div class="app-container">
    <!-- 筛选栏 -->
    <el-card class="filter-container">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="审核状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 150px" @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="待审核" value="0" />
            <el-option label="已通过" value="1" />
            <el-option label="已驳回" value="2" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleFilter">查询</el-button>
        </el-form-item>
        <el-form-item>
           <el-radio-group v-model="viewMode">
             <el-radio-button label="table">列表模式</el-radio-button>
             <el-radio-button label="card">卡片模式</el-radio-button>
           </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区域 -->
    <el-card class="table-container" v-if="viewMode === 'table'">
      <el-table v-loading="loading" :data="tableData" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        
        <el-table-column label="证书图片" width="120" align="center">
          <template #default="{ row }">
            <el-image 
              style="width: 80px; height: 60px" 
              :src="row.imgUrl" 
              :preview-src-list="[row.imgUrl]" 
              fit="cover"
              preview-teleported
            />
          </template>
        </el-table-column>

        <el-table-column prop="studentName" label="学生姓名" width="120" align="center" />
        <el-table-column prop="className" label="班级" width="150" align="center" />
        <el-table-column prop="certName" label="证书名称" min-width="150" align="center" />
        
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="uploadTime" label="上传时间" width="180" align="center" />

        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <div v-if="row.status === 0">
              <el-button type="success" link size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" link size="small" @click="handleReject(row)">驳回</el-button>
            </div>
            <div v-else>
              <el-popover placement="left" title="详情" :width="200" trigger="hover">
                <template #reference>
                  <el-button type="primary" link size="small">查看详情</el-button>
                </template>
                <div>
                  <p v-if="row.status === 2">驳回原因: {{ row.rejectReason }}</p>
                  <p v-else>审核已完成</p>
                  <p>审核时间: {{ new Date().toLocaleString() }}</p>
                </div>
              </el-popover>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 卡片模式 -->
    <div v-else class="card-mode-wrapper">
       <el-empty v-if="!tableData.length" description="暂无待处理数据" />
       
       <div v-else class="card-view-container">
          <CertificateCard 
            :data="currentCert" 
            @approve="handleApprove" 
            @reject="handleReject"
          >
            <template #append-actions>
              <div class="nav-buttons">
                <el-button @click="handlePrev" :disabled="currentIndex <= 0" icon="ArrowLeft">上一个</el-button>
                <el-button @click="handleNext" :disabled="currentIndex >= tableData.length - 1">
                  下一个 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>
          </CertificateCard>

          <div class="pagination-info">
             当前第 {{ currentIndex + 1 }} 条 / 共 {{ tableData.length }} 条
          </div>
       </div>
    </div>


    <!-- 驳回弹窗 -->
    <el-dialog v-model="rejectDialogVisible" title="驳回审核" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="驳回原因">
          <el-input 
            v-model="rejectForm.reason" 
            type="textarea" 
            placeholder="请输入驳回原因" 
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="rejectDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmReject">确认驳回</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { getCertificates, updateStatus } from '@/api/mock/certificate'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import CertificateCard from './components/CertificateCard.vue'
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'

const loading = ref(false)
const tableData = ref([])
const queryParams = reactive({
  status: ''
})

const viewMode = ref('table')
const currentIndex = ref(0)
const currentCert = computed(() => tableData.value[currentIndex.value] || {})

// 驳回相关
const rejectDialogVisible = ref(false)
const rejectForm = reactive({
  id: null,
  reason: ''
})

const getList = async () => {
  loading.value = true
  try {
    const res = await getCertificates(queryParams)
    tableData.value = res.data.list
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  getList()
  currentIndex.value = 0
}

const getStatusType = (status) => {
  const map = {
    0: 'warning',
    1: 'success',
    2: 'danger'
  }
  return map[status]
}

const getStatusText = (status) => {
  const map = {
    0: '待审核',
    1: '已通过',
    2: '已驳回'
  }
  return map[status]
}

// 通过审核
const handleApprove = (row) => {
  ElMessageBox.confirm(
    `确认通过 ${row.studentName} 的 ${row.certName} 申请吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success',
    }
  ).then(async () => {
    try {
      await updateStatus(row.id, 1) // 1: 通过
      ElMessage.success('审核通过')
      getList() // 重新获取列表，界面会根据currentIndex更新
    } catch (error) {
      ElMessage.error('操作失败')
    }
  }).catch(() => {})
}

// 驳回审核
const handleReject = (row) => {
  rejectForm.id = row.id
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectForm.reason) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  try {
    await updateStatus(rejectForm.id, 2, rejectForm.reason)
    ElMessage.success('已驳回')
    rejectDialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// Card Navigation
const handlePrev = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const handleNext = () => {
  if (currentIndex.value < tableData.value.length - 1) currentIndex.value++
}

watch(tableData, (newVal) => {
   if (currentIndex.value >= newVal.length) {
       currentIndex.value = 0
   }
})

onMounted(() => {
  getList()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}
.filter-container {
  margin-bottom: 20px;
}
.card-view-container {
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.pagination-info {
  margin-top: 15px;
  color: #909399;
  font-size: 14px;
}
.nav-buttons {
  margin-left: auto;
  display: flex;
  gap: 10px;
}
</style>
