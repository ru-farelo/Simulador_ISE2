export type LearningItemType = 'vocab' | 'grammar' | 'filler' | 'connector' | 'pronunciation'

export interface DueVocabItem {
  item_id: number
  type: 'vocab'
  category: string
  phase: 'flashcard' | 'production'
  term?: string | null
  translation_es?: string | null
  example?: string | null
  sentence?: string | null
  hint?: string | null
}

export type VocabCategoryFilter = 'general' | 'thematic'

export interface DueGrammarItem {
  item_id: number
  type: 'grammar'
  category: string
  structure: string
  hint: string
  prompt_sentence: string
  instructions: string
}

export interface DueFillerItem {
  item_id: number
  type: 'filler' | 'connector'
  category: string
  target: string
  hint: string
  opener: string
  time_limit_seconds: number
}

export interface DuePronunciationItem {
  item_id: number
  type: 'pronunciation'
  category: string
  sentence: string
  tip: string
}

export type DueItem = DueVocabItem | DueGrammarItem | DueFillerItem | DuePronunciationItem

export interface LearningReviewRequest {
  answer?: string
  prompt?: string
  self_rating?: 'known' | 'unknown'
}

export interface LearningReviewResult {
  correct: boolean
  feedback: string
  corrected_answer: string | null
  interval_days: number
  repetitions: number
  next_due_date: string
}
