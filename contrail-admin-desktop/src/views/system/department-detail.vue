<template>
  <div class="app-container">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600 mr-3"> 部门信息调整 </span>
      </template>
    </el-page-header>

    <div class="main-content">
       <!-- 基础信息 -->
       <el-card class="section-card" header="基础信息">
          <el-form :model="form" label-width="100px" ref="formRef" :rules="rules">
             <el-row :gutter="20">
                <el-col :span="12">
                   <el-form-item label="学院" prop="college">
                      <el-input v-model="form.college" placeholder="请输入学院" />
                   </el-form-item>
                </el-col>
                <el-col :span="12">
                   <el-form-item label="年级" prop="grade">
                      <el-input v-model="form.grade" placeholder="请输入年级 (如 2023级)" />
                   </el-form-item>
                </el-col>
                <el-col :span="12">
                   <el-form-item label="专业" prop="major">
                      <el-input v-model="form.major" placeholder="请输入专业" />
                   </el-form-item>
                </el-col>
                <el-col :span="12">
                   <el-form-item label="班级名称" prop="className">
                      <el-input v-model="form.className" placeholder="请输入班级名称 (如 1班)" />
                   </el-form-item>
                </el-col>
             </el-row>
          </el-form>
       </el-card>

       <!-- 自动加分配置 -->
       <el-card class="section-card" header="加分配置">
          <el-form :model="form" label-width="100px">
             <el-form-item label="自动加分时间">
                <el-date-picker
                   v-model="form.autoScoreTime"
                   type="datetime"
                   placeholder="选择日期时间"
                   value-format="YYYY-MM-DD HH:mm:ss"
                />
                <span class="tip-text">设置后将在该时间点作为执行周期起点开始加分</span>
             </el-form-item>
          </el-form>
       </el-card>

       <!-- 证书配置 -->
       <el-card class="section-card">
          <template #header>
             <div class="card-header">
                <span>证书配置</span>
                <el-button type="primary" size="small" @click="openCertDialog">添加证书</el-button>
             </div>
          </template>

          <el-table :data="certList" border style="width: 100%">
             <el-table-column prop="name" label="证书名称" />
             <el-table-column prop="required" label="是否必选" width="120">
                <template #default="{ row }">
                   <el-tag :type="row.required ? 'danger' : 'info'">{{ row.required ? '必选' : '非必选' }}</el-tag>
                </template>
             </el-table-column>
             <el-table-column label="操作" width="120" align="center">
                <template #default="{ row }">
                   <el-button type="danger" link @click="removeCert(row.id)">移除</el-button>
                </template>
             </el-table-column>
          </el-table>
       </el-card>

       <div class="footer-actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving">保存配置</el-button>
       </div>
    </div>

    <!-- 添加证书弹窗 -->
    <el-dialog v-model="certDialogVisible" title="添加证书" width="500px">
       <el-checkbox-group v-model="selectedCertsToAdd">
          <el-checkbox 
             v-for="cert in allCertTypes" 
             :key="cert.id" 
             :label="cert.id"
             :disabled="isCertBound(cert.id)"
          >
             {{ cert.name }} {{ isCertBound(cert.id) ? '(已添加)' : '' }}
          </el-checkbox>
       </el-checkbox-group>
       <template #footer>
          <span class="dialog-footer">
             <el-button @click="certDialogVisible = false">取消</el-button>
             <el-button type="primary" @click="confirmAddCerts">确定</el-button>
          </span>
       </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDepartmentDetail, updateDepartment, getCertTypes, saveClassCerts } from '@/api/mock/system'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const form = reactive({
  id: Number(id),
  college: '',
  grade: '',
  major: '',
  className: '',
  autoScoreTime: '',
  boundCerts: [] // 存储ID
})

const rules = {
   college: [{ required: true, message: '请输入学院', trigger: 'blur' }],
   grade: [{ required: true, message: '请输入年级', trigger: 'blur' }],
   major: [{ required: true, message: '请输入专业', trigger: 'blur' }],
   className: [{ required: true, message: '请输入班级名称', trigger: 'blur' }]
}

const formRef = ref(null)
const saving = ref(false)
const allCertTypes = ref([])
const certDialogVisible = ref(false)
const selectedCertsToAdd = ref([])

// 计算当前绑定的证书详细信息列表
const certList = computed(() => {
   return allCertTypes.value.filter(c => form.boundCerts.includes(c.id))
})

const loadData = async () => {
   // 获取所有证书类型
   const certRes = await getCertTypes()
   allCertTypes.value = certRes.data

   // 获取部门详情
   const res = await getDepartmentDetail(id)
   const data = res.data
   
   Object.assign(form, {
      college: data.college || '',
      grade: data.grade || '',
      major: data.major || '',
      className: data.className || '',
      autoScoreTime: data.autoScoreTime || '',
      boundCerts: data.boundCerts || []
   })
}

const goBack = () => {
   router.back()
}

const handleSave = async () => {
   await formRef.value.validate(async (valid) => {
      if (valid) {
         saving.value = true
         try {
            await updateDepartment(form)
            // 单独更新证书绑定逻辑（如果是分离接口的话，这里 mock 里 saveClassCerts 是分离的，但 updateDepartment 也应当包含数据更新）
            // 在实际后端中可能是一个接口。这里为了确保 mock 状态一致，我们显式调用证书保存
            await saveClassCerts(form.id, form.boundCerts)
            
            ElMessage.success('保存成功')
            goBack()
         } catch (e) {
            ElMessage.error('保存失败')
         } finally {
            saving.value = false
         }
      }
   })
}

// 证书管理
const openCertDialog = () => {
   selectedCertsToAdd.value = []
   certDialogVisible.value = true
}

const isCertBound = (certId) => {
   return form.boundCerts.includes(certId)
}

const confirmAddCerts = () => {
   form.boundCerts.push(...selectedCertsToAdd.value)
   certDialogVisible.value = false
}

const removeCert = (certId) => {
   ElMessageBox.confirm('确定要移除该证书吗?', '提示', {
      type: 'warning'
   }).then(() => {
      const index = form.boundCerts.indexOf(certId)
      if (index > -1) {
         form.boundCerts.splice(index, 1)
      }
   }).catch(() => {})
}

onMounted(() => {
   loadData()
})
</script>

<style scoped lang="scss">
.app-container {
   padding: 20px;
   background-color: #f0f2f5;
   min-height: 100vh;
}

.main-content {
   margin-top: 20px;
   display: flex;
   flex-direction: column;
   gap: 20px;
}

.section-card {
   :deep(.el-card__header) {
      padding: 15px 20px;
      font-weight: bold;
   }
}

.tip-text {
   margin-left: 10px;
   color: #909399;
   font-size: 12px;
}

.card-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
}

.footer-actions {
   display: flex;
   justify-content: center;
   gap: 20px;
   margin-top: 20px;
   padding-bottom: 40px;
}
</style>
