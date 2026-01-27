<template>
  <div class="app-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>管理员管理</span>
        <el-button style="float: right; padding: 3px 0" type="primary" link>新增管理员</el-button>
      </div>
      <el-table :data="tableData" style="width: 100%" border>
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="username" label="账号" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="role" label="角色" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'super' ? 'warning' : 'success'">
              {{ row.role === 'super' ? '超级管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdmins } from '@/api/mock/system'

const tableData = ref([])

onMounted(async () => {
  const res = await getAdmins()
  tableData.value = res.data
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style>
