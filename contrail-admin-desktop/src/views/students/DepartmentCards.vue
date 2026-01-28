<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col
        v-for="dept in departments"
        :key="dept.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
        class="card-col"
      >
        <el-card shadow="hover" class="dept-card" @click="handleEnterClass(dept.id)">
          <div class="card-content">
            <h3 class="dept-name">{{ dept.name }}</h3>
            <div class="dept-info">
              <el-icon><User /></el-icon>
              <span>{{ dept.studentCount || 0 }} 人</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDepartments } from '@/api/mock/system'
import { User } from '@element-plus/icons-vue'

const router = useRouter()
const departments = ref([])

onMounted(async () => {
  const res = await getDepartments()
  departments.value = res.data
})

const handleEnterClass = (id) => {
  router.push(`/students/class/${id}`)
}
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}
.card-col {
  margin-bottom: 20px;
}
.dept-card {
  cursor: pointer;
  height: 100%;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-5px);
  }
}
.card-content {
  text-align: center;
  padding: 20px 0;
}
.dept-name {
  margin: 0 0 15px;
  font-size: 18px;
  color: #303133;
}
.dept-info {
  display: flex;
  justify-content: center;
  align-items: center;
  color: #909399;
  font-size: 14px;
  
  .el-icon {
    margin-right: 5px;
  }
}
</style>
