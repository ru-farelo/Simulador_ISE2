export type Genre = 'essay' | 'article' | 'letter' | 'review'
export type PromptSource = 'fixed' | 'generated'

export interface WritingPrompt {
  id: string
  source: PromptSource
  genre: Genre
  title: string
  instructions: string
  word_min: number
  word_max: number
}

export interface WritingSubmission {
  prompt_id: string
  genre: Genre
  title: string
  instructions: string
  text: string
  duration_seconds: number
}

export interface ModelSentence {
  original: string
  rewritten: string
  explanation: string
}

export interface ErrorItem {
  category: string
  excerpt: string
  correction: string
  explanation: string
}

export type Band = 'Distinction' | 'Merit' | 'Pass' | 'Not yet'

export interface WritingCorrectionResult {
  session_id: number
  word_count: number
  band: Band
  summary: string
  strengths: string[]
  errors: ErrorItem[]
  model_sentence: ModelSentence
  created_at: string
}
