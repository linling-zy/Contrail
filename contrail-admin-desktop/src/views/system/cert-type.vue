<template>
  <div class="app-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>证书类型管理</span>
        <el-button style="float: right; padding: 3px 0" type="primary" link>添加证书</el-button>
      </div>
      <el-table :data="tableData" style="width: 100%" border>
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="证书名称" />
        <el-table-column prop="required" label="必填项" align="center">
          <template #default="{ row }">
            <el-tag :type="row.required ? 'danger' : 'info'">{{ row.required ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCertTypes } from '@/api/mock/system'

const tableData = ref([])

onMounted(async () => {
  const res = await getCertTypes()
  tableData.value = res.data
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style>
