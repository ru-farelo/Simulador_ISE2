import { api } from './client'
import type {
  SpeakingCorrectionRequest,
  SpeakingCorrectionResult,
  SpeakingTaskName,
  SpeakingTurnRequest,
  SpeakingTurnResponse,
} from '../types/speaking'

export const speakingApi = {
  getConversationTopic: () => api.get<{ topic: string }>('/speaking/conversation/topic'),
  postTurn: (taskName: SpeakingTaskName, request: SpeakingTurnRequest) =>
    api.post<SpeakingTurnResponse>(`/speaking/${taskName}/turn`, request),
  correct: (request: SpeakingCorrectionRequest) =>
    api.post<SpeakingCorrectionResult>('/speaking/correct', request),
}
