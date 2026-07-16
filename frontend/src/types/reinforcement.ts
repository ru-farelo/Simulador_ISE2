export interface DueReinforcementItem {
  id: number
  error_category: string
  example_sentence: string
  is_real: boolean
}

export interface ReinforcementReviewRequest {
  answer: string
}

export interface ReinforcementReviewResult {
  correct: boolean
  feedback: string
  corrected_sentence: string
  interval_days: number
  repetitions: number
  next_due_date: string
}
