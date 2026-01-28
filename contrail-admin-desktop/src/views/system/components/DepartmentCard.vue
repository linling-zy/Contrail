<template>
  <div class="department-card-wrapper">
    <el-card shadow="never" class="department-card">
      <div class="card-content">
        <div class="dept-icon">
          <el-icon :size="64" color="#409EFF"><OfficeBuilding /></el-icon>
        </div>
        
        <div class="dept-info">
          <div class="header">
            <span class="dept-name">{{ data.name }}</span>
            <el-tag :type="getLevelTag(data.level)" effect="dark">
              {{ getLevelName(data.level) }}
            </el-tag>
          </div>

          <div class="meta-info">
             <div class="info-item">
               <span class="label">ID:</span>
               <span class="value">{{ data.id }}</span>
             </div>
             <div class="info-item" v-if="data.children">
               <span class="label">下级节点数:</span>
               <span class="value">{{ data.children.length }}</span>
             </div>
             <div class="info-item" v-if="data.boundCerts">
               <span class="label">已配置证书:</span>
               <span class="value">{{ data.boundCerts.length }} 项</span>
             </div>
          </div>

          <div class="actions">
            <slot name="prepend-actions"></slot>
            
            <template v-if="data.level === 4">
               <el-button type="primary" size="large" icon="Setting" @click="$emit('config', data)">
                 配置证书
               </el-button>
            </template>
            <template v-else>
               <el-button disabled size="large">无需配置</el-button>
            </template>

            <slot name="append-actions"></slot>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { OfficeBuilding, Setting } from '@element-plus/icons-vue'

defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

defineEmits(['config'])

const getLevelTag = (level) => {
  const map = { 1: '', 2: 'success', 3: 'warning', 4: 'danger' }
  return map[level] || 'info'
}

const getLevelName = (level) => {
  const map = { 1: '学院', 2: '年级', 3: '专业', 4: '班级' }
  return map[level] || '节点'
}
</script>

<style scoped lang="scss">
.department-card-wrapper {
  width: 100%;
  height: 100%;
}

.department-card {
  width: 100%;
  height: 100%;
  :deep(.el-card__body) {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }
}

.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
  width: 100%;
  max-width: 800px;
  
  .dept-icon {
    background: #f0f2f5;
    padding: 30px;
    border-radius: 50%;
  }

  .dept-info {
    text-align: center;
    width: 100%;

    .header {
      margin-bottom: 30px;
      .dept-name {
        font-size: 32px;
        font-weight: bold;
        color: #303133;
        margin-right: 15px;
      }
    }

    .meta-info {
      display: flex;
      justify-content: center;
      gap: 40px;
      margin-bottom: 40px;
      
      .info-item {
        font-size: 18px;
        color: #606266;
        .label {
          color: #909399;
          margin-right: 10px;
        }
        .value {
            font-weight: 500;
        }
      }
    }

    .actions {
      display: flex;
      justify-content: center;
      gap: 20px;
    }
  }
}
</style>
