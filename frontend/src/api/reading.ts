import { api } from './client'
import type { ExamSource, ReadingExam, ReadingExamResult, ReadingExamSubmission } from '../types/reading'

export const readingApi = {
  getExam: (mode: ExamSource = 'fixed') => api.get<ReadingExam>(`/reading/exam?mode=${mode}`),
  submit: (submission: ReadingExamSubmission) => api.post<ReadingExamResult>('/reading/submit', submission),
}
