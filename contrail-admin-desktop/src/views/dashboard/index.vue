<template>
  <div class="dashboard-container">
    <!-- Header -->
    <div class="header-section">
      <div class="header-content">
        <h2 class="title">工作台</h2>
        <p class="subtitle">下午好，管理员。今天又是充满活力的一天。</p>
      </div>
      <div class="header-extra">
        <el-button @click="handleLogout">退出登录</el-button>
        <el-button type="primary" icon="Plus" @click="router.push('/students')">新增学员</el-button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="icon-wrapper bg-blue">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-content">
          <span class="label">在籍学员</span>
          <span class="value">{{ stats.totalStudents }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon-wrapper bg-green">
          <el-icon><School /></el-icon>
        </div>
        <div class="stat-content">
          <span class="label">行政班级</span>
          <span class="value">{{ stats.totalClasses }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon-wrapper bg-orange">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="stat-content">
          <span class="label">待办事项</span>
          <span class="value">{{ stats.pendingCount }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon-wrapper bg-purple">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <span class="label">平均积分</span>
          <span class="value">{{ stats.avgScore }}</span>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="main-grid">
      <!-- Left: Pending Review List -->
      <div class="card table-card">
        <div class="card-header">
          <h3>待办审核列表</h3>
          <el-tag type="warning" effect="plain" round size="small">{{ studentList.length }} 待处理</el-tag>
        </div>
        <el-table :data="studentList" :show-header="true" style="width: 100%">
          <el-table-column prop="name" label="学员信息" width="140">
            <template #default="scope">
              <div class="user-cell">
                <div class="avatar-placeholder">{{ scope.row.name.charAt(0) }}</div>
                <div class="user-info">
                  <span class="name">{{ scope.row.name }}</span>
                  <span class="sub">{{ scope.row.className }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="待办事项" min-width="200">
             <template #default="scope">
               <div class="pending-tags">
                 <el-tag 
                    v-if="scope.row.status.preliminary === 'pending'"
                    size="small" 
                    type="info" 
                    effect="light"
                    class="pending-tag"
                  >初试</el-tag>
                  <el-tag 
                    v-if="scope.row.status.medical === 'pending'"
                    size="small" 
                    type="warning" 
                    effect="light"
                    class="pending-tag"
                  >体检</el-tag>
                  <el-tag 
                    v-if="scope.row.status.political === 'pending'"
                    size="small" 
                    type="danger" 
                    effect="light"
                    class="pending-tag"
                  >政审</el-tag>
                  <el-tag 
                    v-if="scope.row.status.admission === 'pending'"
                    size="small" 
                    type="primary" 
                    effect="light"
                    class="pending-tag"
                  >录取</el-tag>
               </div>
             </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="right">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="router.push(`/students?id=${scope.row.id}`)">去审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Right: Recruitment Status Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3>状态分布 - 平行维度</h3>
        </div>
        <div ref="chartRef" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { getDashboardStats } from '@/api/dashboard'
import { User, School, Timer, TrendCharts, Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()
const chartRef = ref(null)

const stats = reactive({
  totalStudents: 0,
  totalClasses: 0,
  pendingCount: 0,
  avgScore: 0,
  // Detailed counts for each stage
  details: {
    admission: { qualified: 0, pending: 0, failed: 0 },
    medical: { qualified: 0, pending: 0, failed: 0 },
    vetted: { qualified: 0, pending: 0, failed: 0 }
  }
})

const studentList = ref([])

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const getStageName = (key) => {
  const map = {
    admission: '录取',
    medical: '体检',
    vetted: '政审'
  }
  return map[key] || key
}

const initChart = () => {
  if (!chartRef.value) return
  const myChart = echarts.init(chartRef.value)
  
  const stages = ['admission', 'medical', 'vetted']
  const stageNames = stages.map(s => getStageName(s))
  
  // Extract data for series
  const qualifiedData = stages.map(s => stats.details[s].qualified)
  const pendingData = stages.map(s => stats.details[s].pending)
  const failedData = stages.map(s => stats.details[s].failed)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['合格', '进行中', '未通过'],
      bottom: 0,
      icon: 'circle',
      itemGap: 24,
      textStyle: { color: '#6b7280' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      splitLine: { show: false },
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'category',
      data: stageNames,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#374151',
        fontWeight: 500
      }
    },
    series: [
      {
        name: '合格',
        type: 'bar',
        stack: 'total',
        label: { show: true, formatter: (p) => p.value > 0 ? p.value : '' },
        emphasis: { focus: 'series' },
        data: qualifiedData,
        itemStyle: { color: '#34D399', borderRadius: [0, 0, 0, 0] }, // Emerald 400
        barWidth: 24
      },
      {
        name: '进行中',
        type: 'bar',
        stack: 'total',
        label: { show: true, formatter: (p) => p.value > 0 ? p.value : '', color: '#9CA3AF' },
        emphasis: { focus: 'series' },
        data: pendingData,
        itemStyle: { color: '#E5E7EB' } // Gray 200
      },
      {
        name: '未通过',
        type: 'bar',
        stack: 'total',
        label: { show: true, formatter: (p) => p.value > 0 ? p.value : '' },
        emphasis: { focus: 'series' },
        data: failedData,
        itemStyle: { color: '#F87171', borderRadius: [0, 6, 6, 0] } // Red 400
      }
    ]
  }

  myChart.setOption(option)
  
  window.addEventListener('resize', () => {
    myChart.resize()
  })
}

const loadData = async () => {
  try {
    // 调用后端统计接口
    const res = await getDashboardStats()
    
    if (res.code === 200 && res.data) {
      const data = res.data
      
      // 更新统计数据
      stats.totalStudents = data.total_students || 0
      stats.totalClasses = data.total_departments || 0
      
      // 处理阶段状态统计
      const processStats = data.process_stats || {}
      const stages = ['admission', 'medical', 'vetted']
      
      // 初始化详情数据
      const tempDetails = {
        admission: { qualified: 0, pending: 0, failed: 0 },
        medical: { qualified: 0, pending: 0, failed: 0 },
        vetted: { qualified: 0, pending: 0, failed: 0 }
      }
      
      // 计算待办事项总数（所有阶段中状态为 pending 的数量）
      let pendingCount = 0
      
      stages.forEach(stage => {
        const stageStats = processStats[stage] || {}
        // 状态映射：0=待定(pending), 1=通过(qualified), 2=不通过(unqualified/failed)
        tempDetails[stage].pending = stageStats[0] || 0
        tempDetails[stage].qualified = stageStats[1] || 0
        tempDetails[stage].failed = stageStats[2] || 0
        
        pendingCount += tempDetails[stage].pending
      })
      
      stats.details = tempDetails
      stats.pendingCount = pendingCount
      
      // 平均积分暂时设为 0（后端接口未返回，如需可后续添加）
      stats.avgScore = 0
      
      // 待办审核列表暂时为空（后端接口未返回，如需可后续添加或单独调用接口）
      studentList.value = []
      
      nextTick(() => {
        initChart()
      })
    } else {
      console.error('获取统计数据失败:', res.message || '未知错误')
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* Dashboard Container */
.dashboard-container {
  padding: 24px 32px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--el-text-color-primary);
  transition: background-color 0.3s;
}

/* Header */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.header-content .title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--el-text-color-primary);
}

.header-content .subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  border: 1px solid var(--el-border-color-light);
  transition: all 0.2s;
}

.stat-card:hover {
  box-shadow: var(--el-box-shadow-light);
  transform: translateY(-2px);
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 20px;
}

/* Use Element Plus theme vars for automated dark mode support */
.bg-blue { background-color: var(--el-color-primary-light-9); color: var(--el-color-primary); }
.bg-green { background-color: var(--el-color-success-light-9); color: var(--el-color-success); }
.bg-orange { background-color: var(--el-color-warning-light-9); color: var(--el-color-warning); }
.bg-purple { background-color: var(--el-color-danger-light-9); color: var(--el-color-danger); }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-content .label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-content .value {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.card {
  background: var(--el-bg-color);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--el-text-color-primary);
}

/* Table Styles */
.user-cell {
  display: flex;
  align-items: center;
}

.avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  margin-right: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-info .name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.user-info .sub {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.pending-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pending-tag {
  border: none;
  font-weight: 500;
}

/* Chart Styles */
.chart-container {
  height: 300px;
  width: 100%;
}
</style>
