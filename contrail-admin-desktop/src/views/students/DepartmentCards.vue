<template>
  <div class="student-entry-container">
    <!-- 1. Glass Header -->
    <header class="glass-header">
       <div class="header-content">
          <div class="brand">
             <div class="icon-box">
                <el-icon><School /></el-icon>
             </div>
             <div>
                <h1 class="page-title">学生管理</h1>
                <p class="subtitle">选择班级或部门以管理学生档案</p>
             </div>
          </div>
          
          <div class="search-bar">
             <el-input 
               v-model="searchQuery" 
               placeholder="搜索部门..." 
               prefix-icon="Search"
               class="glass-input"
               clearable
             />
          </div>
       </div>
    </header>

    <!-- 2. Bento Grid -->
    <div class="bento-scroll-area">
       <!-- Empty State -->
       <div v-if="filteredDepartments.length === 0" class="empty-state">
           <el-empty description="未找到相关部门" :image-size="120" />
       </div>

       <div v-else class="bento-grid">
          <div 
             v-for="(dept, index) in filteredDepartments"
             :key="dept.id"
             class="bento-card"
             :class="getCardClass(index, dept)"
             @click="handleEnterClass(dept.id)"
          >
             <div class="card-bg-decoration"></div>
             
             <div class="card-content">
                <div class="dept-header">
                   <h3 class="dept-name">{{ dept.name }}</h3>
                   <el-icon class="arrow-icon"><Right /></el-icon>
                </div>
                
                <div class="dept-metrics">
                   <div class="metric-item">
                      <span class="label">学生总数</span>
                      <span class="value">{{ dept.studentCount || 0 }}</span>
                   </div>
                   <!-- Optional: Add more metrics if available in future -->
                </div>
                
                <div class="dept-footer">
                   <el-tag size="small" effect="dark" round class="id-tag">ID: {{ dept.id }}</el-tag>
                </div>
             </div>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getDepartments } from '@/api/system'
import { School, Search, Right } from '@element-plus/icons-vue'

const router = useRouter()
const departments = ref([])
const searchQuery = ref('')

onMounted(async () => {
  try {
    const res = await getDepartments({ per_page: 100 })
    
    if (res.items) {
      departments.value = res.items.map(dept => ({
        id: dept.id,
        name: dept.class_name || `${dept.college || ''}${dept.grade || ''}${dept.major || ''}${dept.class_name || ''}`.trim() || '未命名部门',
        studentCount: dept.student_count || 0,
        college: dept.college,
        grade: dept.grade,
        major: dept.major,
        className: dept.class_name
      }))
    } else if (res.data) {
      departments.value = Array.isArray(res.data) ? res.data : []
    } else {
      departments.value = []
    }
  } catch (error) {
    console.error('加载部门列表失败:', error)
    departments.value = []
  }
})

const filteredDepartments = computed(() => {
   if (!searchQuery.value) return departments.value
   const query = searchQuery.value.toLowerCase()
   return departments.value.filter(d => d.name.toLowerCase().includes(query))
})

// Visual Logic: Make the first few cards larger or interesting
const getCardClass = (index, dept) => {
   // Make all cards uniform size for consistency
   if (index === 0) return 'theme-blue'
   if (index === 1) return 'theme-purple'
   if (index % 5 === 0) return 'theme-orange'
   return 'theme-default'
}

const handleEnterClass = (id) => {
  router.push(`/students/class/${id}`)
}
</script>

<style scoped lang="scss">
.student-entry-container {
  height: calc(100vh - 84px);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
  font-family: 'Inter', system-ui, sans-serif;
  overflow: hidden;
  transition: background-color 0.3s;
}

/* Glass Header */
.glass-header {
   padding: 24px 40px;
   background: var(--el-bg-color);
   border-bottom: 1px solid var(--el-border-color-light);
   z-index: 10;
   transition: background-color 0.3s;
   
   .header-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .brand {
         display: flex;
         gap: 16px;
         align-items: center;
         
         .icon-box {
            width: 48px;
            height: 48px;
            background: var(--el-color-primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            box-shadow: var(--el-box-shadow-light);
         }
         
         .page-title { margin: 0; font-size: 24px; font-weight: 800; color: var(--el-text-color-primary); letter-spacing: -0.5px; }
         .subtitle { margin: 4px 0 0; font-size: 13px; color: var(--el-text-color-secondary); }
      }
      
      .search-bar {
         width: 300px;
         
         .glass-input :deep(.el-input__wrapper) {
            border-radius: 20px;
            background: var(--el-fill-color-light);
            box-shadow: 0 0 0 1px var(--el-border-color-light) inset;
            border: 1px solid transparent;
            transition: all 0.2s;
            
            &:hover, &.is-focus {
               background: var(--el-bg-color);
               box-shadow: 0 0 0 1px var(--el-color-primary) inset;
            }
         }
      }
   }
}

/* Bento Area */
.bento-scroll-area {
   flex: 1;
   overflow-y: auto;
   padding: 40px;
}

.bento-grid {
   display: grid;
   grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
   gap: 24px;
   max-width: 1400px;
   margin: 0 auto;
   padding-bottom: 40px;
}

/* Card Styles */
.bento-card {
   background: var(--el-bg-color);
   border-radius: 24px;
   padding: 24px;
   cursor: pointer;
   position: relative;
   overflow: hidden;
   border: 1px solid var(--el-border-color-light);
   box-shadow: var(--el-box-shadow-light);
   transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   display: flex;
   flex-direction: column;
   min-height: 200px;
   
   &:hover {
      transform: translateY(-8px);
      box-shadow: var(--el-box-shadow);
      border-color: var(--el-color-primary-light-5);
      
      .arrow-icon { opacity: 1; transform: translateX(0); }
   }
   
   /* Card Themes */
   &.theme-blue { background: var(--el-color-primary-light-9); }
   &.theme-purple { background: var(--el-color-primary-light-8); } 
   &.theme-orange { background: var(--el-color-warning-light-9); }
   
   /* Spans */
   &.span-2-col { grid-column: span 2; }
   
   @media (max-width: 768px) {
      &.span-2-col { grid-column: span 1; }
   }

   .card-content {
      position: relative;
      z-index: 2;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
   }
   
   .dept-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
      
      .dept-name {
         margin: 0;
         font-size: 20px;
         font-weight: 700;
         color: var(--el-text-color-primary);
         line-height: 1.3;
      }
      
      .arrow-icon {
         font-size: 20px;
         color: var(--el-text-color-secondary);
         opacity: 0;
         transform: translateX(-10px);
         transition: all 0.3s;
      }
   }
   
   .dept-metrics {
      flex: 1;
      display: flex;
      align-items: flex-end;
      margin-bottom: 20px;
      
      .metric-item {
         display: flex;
         flex-direction: column;
         
         .value {
            font-size: 48px;
            font-weight: 800;
            line-height: 1;
            color: var(--el-text-color-primary);
            letter-spacing: -2px;
         }
         .label {
            font-size: 13px;
            color: var(--el-text-color-secondary);
            font-weight: 500;
            margin-top: 4px;
         }
      }
   }
   
   .dept-footer {
       .id-tag { border: none; background: rgba(0,0,0,0.05); color: #6b7280; font-weight: 600; }
   }
   
   .card-bg-decoration {
      position: absolute;
      top: -50%;
      right: -20%;
      width: 300px;
      height: 300px;
      background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
      pointer-events: none;
      z-index: 1;
   }
}

.empty-state {
   height: 100%;
   display: flex;
   align-items: center;
   justify-content: center;
}
</style>
