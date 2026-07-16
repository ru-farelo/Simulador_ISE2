import { api } from './client'
import type { PlannerToday } from '../types/planner'

export const plannerApi = {
  getToday: () => api.get<PlannerToday>('/planner/today'),
}
