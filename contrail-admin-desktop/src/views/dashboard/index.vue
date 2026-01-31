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
import { getStudents } from '@/api/mock/student'
import { getDepartments } from '@/api/mock/system'
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
    preliminary: { qualified: 0, pending: 0, failed: 0 },
    medical: { qualified: 0, pending: 0, failed: 0 },
    political: { qualified: 0, pending: 0, failed: 0 },
    admission: { qualified: 0, pending: 0, failed: 0 }
  }
})

const studentList = ref([])

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const getStageName = (key) => {
  const map = {
    preliminary: '初试',
    medical: '体检',
    political: '政审',
    admission: '录取'
  }
  return map[key] || key
}

const initChart = () => {
  if (!chartRef.value) return
  const myChart = echarts.init(chartRef.value)
  
  const stages = ['preliminary', 'medical', 'political', 'admission']
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
    const [stuRes, deptRes] = await Promise.all([
      getStudents({}),
      getDepartments()
    ])

    const students = stuRes.data.list
    const depts = deptRes.data

    stats.totalStudents = students.length
    stats.totalClasses = depts.length

    let pending = 0
    let totalScoreSum = 0
    
    // Initialize details
    const tempDetails = {
      preliminary: { qualified: 0, pending: 0, failed: 0 },
      medical: { qualified: 0, pending: 0, failed: 0 },
      political: { qualified: 0, pending: 0, failed: 0 },
      admission: { qualified: 0, pending: 0, failed: 0 }
    }

    const stages = ['preliminary', 'medical', 'political', 'admission']
    const pendingList = []

    students.forEach(s => {
      let hasPending = false
      
      // General pending count
      Object.values(s.status || {}).forEach(status => {
        if (status === 'pending') {
            pending++
            hasPending = true
        }
      })
      totalScoreSum += s.totalScore

      if (hasPending) {
        pendingList.push(s)
      }

      // Count for each stage
      stages.forEach(stage => {
        const status = s.status?.[stage] || 'pending'
        if (status === 'qualified') tempDetails[stage].qualified++
        else if (status === 'failed') tempDetails[stage].failed++
        else tempDetails[stage].pending++
      })
    })

    // Update list to show pending students
    studentList.value = pendingList.slice(0, 7)

    stats.details = tempDetails
    stats.pendingCount = pending
    stats.avgScore = students.length ? Math.round(totalScoreSum / students.length) : 0

    nextTick(() => {
      initChart()
    })

  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px 32px;
  background-color: #f7f9fc;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #1f2d3d;
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
  color: #111827;
}

.header-content .subtitle {
  font-size: 14px;
  color: #6b7280;
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
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.01), 0 1px 2px -1px rgba(0, 0, 0, 0.01);
  border: 1px solid #f3f4f6;
  transition: all 0.2s;
}

.stat-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.01);
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

.bg-blue { background-color: #eff6ff; color: #3b82f6; }
.bg-green { background-color: #f0fdf4; color: #22c55e; }
.bg-orange { background-color: #fff7ed; color: #f97316; }
.bg-purple { background-color: #faf5ff; color: #a855f7; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-content .label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-content .value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
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
  color: #374151;
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
  background: #e0e7ff;
  color: #4f46e5;
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
  color: #111827;
}

.user-info .sub {
  font-size: 12px;
  color: #9ca3af;
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
