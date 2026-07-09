import { api } from './client'
import type { DashboardSummary } from '../types/dashboard'

export const dashboardApi = {
  getSummary: () => api.get<DashboardSummary>('/dashboard/summary'),
}
