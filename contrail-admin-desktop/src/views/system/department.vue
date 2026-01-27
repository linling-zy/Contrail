<template>
  <div class="app-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>组织架构与证书配置</span>
      </div>
      
      <el-table
        :data="deptData"
        style="width: 100%; margin-bottom: 20px;"
        row-key="id"
        border
        default-expand-all
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column prop="name" label="名称" width="300" />
        
        <el-table-column prop="level" label="层级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelTag(row.level)">{{ getLevelName(row.level) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" align="center">
          <template #default="{ row }">
            <el-button 
              v-if="row.level === 4" 
              type="primary" 
              link 
              icon="Setting" 
              @click="handleConfig(row)"
            >
              配置证书
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 证书配置弹窗 -->
    <el-dialog v-model="configVisible" title="配置班级证书" width="600px">
      <div style="text-align: center">
        <el-transfer
          v-model="currentBoundCerts"
          :data="allCertTypes"
          :titles="['可选证书', '已选证书']"
          :props="{ key: 'id', label: 'name' }"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configVisible = false">取消</el-button>
          <el-button type="primary" @click="saveConfig">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDepartments, getCertTypes, saveClassCerts } from '@/api/mock/system'
import { ElMessage } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'

const deptData = ref([])
const allCertTypes = ref([])

// 配置相关
const configVisible = ref(false)
const currentClassId = ref(null)
const currentBoundCerts = ref([])

const loadData = async () => {
  const deptRes = await getDepartments()
  deptData.value = deptRes.data
  
  const certRes = await getCertTypes()
  allCertTypes.value = certRes.data
}

const getLevelTag = (level) => {
  const map = { 1: '', 2: 'success', 3: 'warning', 4: 'danger' }
  return map[level] || 'info'
}

const getLevelName = (level) => {
  const map = { 1: '学院', 2: '年级', 3: '专业', 4: '班级' }
  return map[level] || '节点'
}

const handleConfig = (row) => {
  currentClassId.value = row.id
  // row.boundCerts 是 mock 数据里的数组，浅拷贝过来
  currentBoundCerts.value = [...(row.boundCerts || [])]
  configVisible.value = true
}

const saveConfig = async () => {
  try {
    await saveClassCerts(currentClassId.value, currentBoundCerts.value)
    ElMessage.success('配置已保存')
    configVisible.value = false
    // 重新加载以更新本地数据（Mock是内存的，所以需要重新Get）
    loadData()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style>
