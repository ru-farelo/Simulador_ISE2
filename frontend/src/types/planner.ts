export interface PlannerBlock {
  type: string
  label: string
  due_count: number
}

export interface ErrorCategoryCount {
  category: string
  count: number
}

export interface PlannerToday {
  date: string
  blocks: PlannerBlock[]
  total_due: number
  top_error_categories: ErrorCategoryCount[]
  suggestion: string
}
