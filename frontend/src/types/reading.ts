export interface Labelled {
  id: string
  text: string
}

export interface MatchingExercise {
  kind: 'matching'
  instructions: string
  items: Labelled[]
  options: Labelled[]
  allow_repeat_options: boolean
}

export interface TrueFalseExercise {
  kind: 'true_false'
  instructions: string
  statements: Labelled[]
}

export interface MultiSelectExercise {
  kind: 'multi_select'
  instructions: string
  options: Labelled[]
  select_count: number
}

export interface GapFillExercise {
  kind: 'gap_fill'
  instructions: string
  items: Labelled[]
}

export interface ReadingTask1 {
  title: string
  paragraphs: Labelled[]
  exercise_a: MatchingExercise
  exercise_b: GapFillExercise
  exercise_c: TrueFalseExercise
  exercise_d: GapFillExercise
}

export interface ReadingTask2 {
  title: string
  texts: Labelled[]
  exercise_a: MatchingExercise
  exercise_b: MultiSelectExercise
  exercise_c: GapFillExercise
}

export interface ReadingTask3 {
  title: string
  texts: Labelled[]
  exercise_1_5: MatchingExercise
  exercise_6_10: MultiSelectExercise
}

export type ExamSource = 'fixed' | 'generated'

export interface ReadingExam {
  id: string
  source: ExamSource
  task1: ReadingTask1
  task2: ReadingTask2
  task3: ReadingTask3
}

export interface Task1Submission {
  exercise_a: Record<string, string>
  exercise_b: Record<string, string>
  exercise_c: Record<string, boolean>
  exercise_d: Record<string, string>
}

export interface Task2Submission {
  exercise_a: Record<string, string>
  exercise_b: string[]
  exercise_c: Record<string, string>
}

export interface Task3Submission {
  exercise_1_5: Record<string, string>
  exercise_6_10: string[]
}

export interface ReadingExamSubmission {
  exam_id: string
  task1: Task1Submission
  task2: Task2Submission
  task3: Task3Submission
  duration_seconds: number
}

export type Band = 'Distinction' | 'Merit' | 'Pass' | 'Not yet'

export interface ItemFeedback {
  id: string
  correct: boolean
  expected?: string | null
  comment?: string | null
}

export interface ExerciseResult {
  label: string
  correct_count: number
  total_count: number
  items: ItemFeedback[]
}

export interface TaskResult {
  task_number: number
  title: string
  exercises: ExerciseResult[]
  correct_count: number
  total_count: number
}

export interface ErrorItem {
  category: string
  excerpt: string
  correction: string
  explanation: string
}

export interface ReadingExamResult {
  session_id: number
  overall_score: number
  band: Band
  summary: string
  tasks: TaskResult[]
  errors: ErrorItem[]
  created_at: string
}
