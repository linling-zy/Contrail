/**
 * 仪表盘相关 API
 */
import { get } from '@/utils/request'

/**
 * 获取仪表盘统计数据
 * @returns {Promise<Object>}
 */
export function getDashboardStats() {
  return get('/api/admin/dashboard/stats')
}



