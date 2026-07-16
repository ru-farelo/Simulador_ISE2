export type Role = 'examiner' | 'candidate'
export type SpeakingTaskName = 'topic' | 'collaborative' | 'conversation'
export type PartName = SpeakingTaskName | 'listening'

export interface ConversationTurn {
  role: Role
  text: string
}

export interface SpeakingTurnRequest {
  history: ConversationTurn[]
  context: Record<string, string>
  conversation_id: string
}

export interface SpeakingTurnResponse {
  examiner_text: string
  task_complete: boolean
}

export type PassageSource = 'fixed' | 'generated'

export interface ListeningPassage {
  id: string
  source: PassageSource
  topic: string
  text: string
  general_question: string
  detail_question: string
}

export interface SpeakingPart {
  task_name: PartName
  transcript: ConversationTurn[]
  conversation_id?: string
}

export interface SpeakingCorrectionRequest {
  parts: SpeakingPart[]
  duration_seconds: number
}

export interface ErrorItem {
  category: string
  excerpt: string
  correction: string
  explanation: string
}

export type Band = 'Distinction' | 'Merit' | 'Pass' | 'Not yet'

export interface SpeakingCorrectionResult {
  session_id: number
  score: number
  band: Band
  summary: string
  structure_comment: string
  grammar_comment: string
  fluency_comment: string
  interaction_comment: string
  errors: ErrorItem[]
  created_at: string
}
