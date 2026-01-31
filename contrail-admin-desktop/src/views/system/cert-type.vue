<template>
  <div class="app-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>证书类型管理</span>
        <el-button style="float: right; padding: 3px 0" type="primary" link @click="handleAdd">添加证书</el-button>
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

    <el-dialog v-model="dialogVisible" title="新增证书类型" width="500px">
      <el-form :model="form" ref="formRef" label-width="100px" :rules="rules">
        <el-form-item label="证书名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入证书名称" />
        </el-form-item>
        <el-form-item label="是否必填" prop="required">
          <el-switch v-model="form.required" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getCertTypes, addCertType } from '@/api/mock/system'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  required: false
})

const rules = {
  name: [{ required: true, message: '请输入证书名称', trigger: 'blur' }]
}

const loadData = async () => {
  const res = await getCertTypes()
  tableData.value = res.data
}

const handleAdd = () => {
  form.name = ''
  form.required = false
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await addCertType({ ...form })
        ElMessage.success('添加成功')
        dialogVisible.value = false
        loadData()
      } catch (e) {
        ElMessage.error('添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
.clearfix:before,
.clearfix:after {
  display: table;
  content: "";
}
.clearfix:after {
  clear: both
}
</style>
