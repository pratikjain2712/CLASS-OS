export type Role = 'platform_admin' | 'institute_admin' | 'branch_admin' | 'teacher'

export interface AuthUser {
  id: string
  name: string
  email: string
  role: Role
  institute_id: string
  branch_id: string | null
}

export interface Publisher {
  id: string
  name: string
  logo_url: string | null
}

export interface Book {
  id: string
  publisher_id: string
  title: string
  subject: string
  class_: number
  board: string
  edition: string | null
}

export interface Chapter {
  id: string
  book_id: string
  chapter_number: number
  chapter_name: string
  processing_status: string
  subtopics: Subtopic[]
}

export interface Subtopic {
  id: string
  number: number
  title: string
  page_start?: number
  page_end?: number
}

export interface TemplateSection {
  id: string
  section_label: string
  question_type: string
  marks_per_question: number
  question_count: number
  difficulty_mix: Record<string, number>
  sort_order: number
}

export interface Template {
  id: string
  name: string
  total_marks: number
  is_system_default: boolean
  sections: TemplateSection[]
}

export interface Question {
  id: string
  source_type: string
  chapter_id: string | null
  publisher_id: string | null
  subject: string
  class_: number
  board: string
  question_type: string
  marks: number
  difficulty: 'Easy' | 'Medium' | 'Hard'
  cognitive_level: string | null
  language: string
  question_text: string
  options: Array<{ key: string; text: string }> | null
  answer: string
  solution: string | null
  has_media: boolean
  media: unknown[]
  concept_tags: string[]
  usage_count: number
  is_approved: boolean
  already_asked: boolean
}

export interface PaperQuestion {
  id: string
  section_label: string
  question_order: number
  marks: number
  set_variant: string
  question: Question
}

export interface Paper {
  id: string
  institute_id: string
  branch_id: string | null
  created_by: string
  title: string
  class_: number
  section: string | null
  subject: string
  board: string
  publisher_id: string | null
  template_id: string | null
  chapter_ids: string[]
  generation_mode: string
  language: string
  total_marks: number | null
  status: string
  created_at: string
  updated_at: string
}

export interface PaperWithQuestions extends Paper {
  paper_questions: PaperQuestion[]
  shortfall: ShortfallItem[]
}

export interface ShortfallItem {
  section_label: string
  question_type: string
  marks: number
  requested: number
  available: number
}

export interface GenerateRequest {
  title: string
  class_: number
  section?: string
  subject: string
  board: string
  publisher_id: string
  template_id: string
  chapter_ids: string[]
  difficulty: string
  generation_mode: string
  language?: string
}
