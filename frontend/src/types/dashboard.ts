export interface SkillProgress {
  sessions: number
  avg_score: number | null
}

export interface DayActivity {
  date: string
  skills_practiced: string[]
}

export interface ErrorCategoryCount {
  category: string
  count: number
}

export interface DashboardSummary {
  streak_days: number
  weekly_activity: DayActivity[]
  skill_progress: Record<string, SkillProgress>
  top_error_categories: ErrorCategoryCount[]
  total_sessions: number
}
