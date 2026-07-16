import { api } from './client'
import type {
  DueReinforcementItem,
  ReinforcementReviewRequest,
  ReinforcementReviewResult,
} from '../types/reinforcement'

export const reinforcementApi = {
  getDue: (limit = 5) => api.get<DueReinforcementItem[]>(`/reinforcement/due?limit=${limit}`),
  review: (itemId: number, request: ReinforcementReviewRequest) =>
    api.post<ReinforcementReviewResult>(`/reinforcement/${itemId}/review`, request),
}
