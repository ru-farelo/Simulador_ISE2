import { api } from './client'
import type { PromptSource, WritingCorrectionResult, WritingPrompt, WritingSubmission } from '../types/writing'

export const writingApi = {
  getPrompt: (mode: PromptSource = 'fixed') => api.get<WritingPrompt>(`/writing/prompt?mode=${mode}`),
  submit: (submission: WritingSubmission) => api.post<WritingCorrectionResult>('/writing/submit', submission),
}
