<template>
  <div class="app-container" :class="{'is-embedded': !!deptId}">
    <el-page-header @back="goBack" title="返回" v-if="!deptId">
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

        <el-card class="section-card" header="加分配置">
          <el-form :model="form" label-width="100px">
              <el-form-item label="基础分" prop="baseScore">
                <el-input-number v-model="form.baseScore" :min="0" :max="100" placeholder="默认80" />
                <span class="tip-text">设置后，新加入该部门学生的初始基础分将以此为准</span>
              </el-form-item>
              <el-form-item label="自动加分时间">
                <el-date-picker
                    v-model="form.autoScoreTime"
                    type="datetime"
                    placeholder="选择日期时间"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    :disabled-date="disabledDate"
                />
                <span class="tip-text">设置后将在该时间点作为执行周期起点开始加分（只能选择今天及以后的日期）</span>
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
import { getDepartmentDetail, updateDepartment, getCertTypes, bindCertificateTypesToDepartment } from '@/api/system'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  deptId: {
    type: [Number, String],
    default: null
  },
  modelValue: { // for v-model binding of visibility if needed, or just to signal mode
     type: Boolean, 
     default: false
  }
})

const emit = defineEmits(['close', 'update:modelValue'])

const route = useRoute()
const router = useRouter()
// ID priority: prop > route param
const id = computed(() => props.deptId || route.params.id)

const form = reactive({
  id: '', // Will be set in loadData
  college: '',
  grade: '',
  major: '',
  className: '',
  autoScoreTime: '',
  baseScore: 80,
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

// 禁用今天之前的日期
const disabledDate = (time) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return time.getTime() < today.getTime()
}

// 计算当前绑定的证书详细信息列表
const certList = computed(() => {
   return allCertTypes.value.filter(c => form.boundCerts.includes(c.id))
})

const loadData = async () => {
   if (!id.value) return // If no ID, can't load
   try {
      // 获取所有证书类型
      const certRes = await getCertTypes()
      
      // 适配后端返回的数据格式：{ certificate_types: [...] }
      if (certRes.certificate_types) {
         allCertTypes.value = certRes.certificate_types.map(item => ({
            id: item.id,
            name: item.name,
            required: item.is_required !== false,
            description: item.description || ''
         }))
      } else if (certRes.data && Array.isArray(certRes.data)) {
         // Mock 数据格式（兼容）
         allCertTypes.value = certRes.data
      } else {
         allCertTypes.value = []
      }

      // 获取部门详情
      const res = await getDepartmentDetail(id.value)
      
      // 适配后端返回的数据格式：{ department: {...} }
      const dept = res.department || res.data || {}
      
      // 获取绑定的证书类型ID列表
      const boundCertIds = dept.certificate_types ? dept.certificate_types.map(ct => ct.id) : []
      
      form.id = Number(id.value) // Ensure internal ID matches
      Object.assign(form, {
         college: dept.college || '',
         grade: dept.grade || '',
         major: dept.major || '',
         className: dept.class_name || '',
         autoScoreTime: dept.bonus_start_date ? `${dept.bonus_start_date} 00:00:00` : '',
         baseScore: dept.base_score !== undefined ? dept.base_score : 80,
         boundCerts: boundCertIds
      })
   } catch (error) {
      console.error('加载数据失败:', error)
      ElMessage.error(error.message || '加载数据失败')
   }
}

const goBack = () => {
   if (props.deptId) {
       emit('close')
       emit('update:modelValue', false)
   } else {
       router.back()
   }
}

const handleSave = async () => {
   await formRef.value.validate(async (valid) => {
      if (valid) {
         saving.value = true
         try {
            // 更新部门基本信息
            const updateData = {
               college: form.college || null,
               grade: form.grade || null,
               major: form.major || null,
               class_name: form.className || null,
               base_score: form.baseScore
            }
            
            // 处理自动加分时间（bonus_start_date）
            if (form.autoScoreTime) {
               // 从 datetime 字符串中提取日期部分
               updateData.bonus_start_date = form.autoScoreTime.split(' ')[0]
            } else {
               updateData.bonus_start_date = null
            }
            
            await updateDepartment(form.id, updateData)
            
            // 单独更新证书绑定
            await bindCertificateTypesToDepartment(form.id, form.boundCerts)
            
            ElMessage.success('保存成功')
            goBack()
         } catch (error) {
            console.error('保存失败:', error)
            ElMessage.error(error.message || error.error || '保存失败')
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

// Watch for prop changes if used as a component
import { watch } from 'vue'
watch(() => props.deptId, (newVal) => {
    if (newVal) {
        loadData()
    }
})
</script>

<style scoped lang="scss">
.app-container {
   padding: 20px;
   background-color: var(--el-bg-color-page);
   min-height: 100vh;
   transition: all 0.3s ease;
   
   &.is-embedded {
       padding: 0;
       background-color: transparent; // Let parent background show or be managed by drawer
       min-height: auto;
   }
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
   color: var(--el-text-color-secondary);
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
