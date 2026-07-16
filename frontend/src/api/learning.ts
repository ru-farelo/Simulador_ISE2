import { api } from './client'
import type {
  DueItem,
  LearningItemType,
  LearningReviewRequest,
  LearningReviewResult,
  VocabCategoryFilter,
} from '../types/learning'

export const learningApi = {
  getDue: (type: LearningItemType, limit = 5, category?: VocabCategoryFilter) =>
    api.get<DueItem[]>(
      `/learning/due?type=${type}&limit=${limit}${category ? `&category=${category}` : ''}`,
    ),
  review: (itemId: number, request: LearningReviewRequest) =>
    api.post<LearningReviewResult>(`/learning/${itemId}/review`, request),
}
