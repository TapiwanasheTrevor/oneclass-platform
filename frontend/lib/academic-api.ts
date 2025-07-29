/**
 * Academic Management API Client
 * Comprehensive API client for academic management operations
 */

import { ApiClient } from './api'

// =====================================================
// TYPES AND INTERFACES
// =====================================================

// Enums
export enum GradingScale {
  A = 'A',
  B = 'B',
  C = 'C',
  D = 'D',
  E = 'E',
  U = 'U'
}

export enum AttendanceStatus {
  PRESENT = 'present',
  ABSENT = 'absent',
  LATE = 'late',
  EXCUSED = 'excused'
}

export enum AssessmentType {
  TEST = 'test',
  QUIZ = 'quiz',
  ASSIGNMENT = 'assignment',
  PROJECT = 'project',
  PRACTICAL = 'practical',
  ORAL = 'oral',
  EXAM = 'exam'
}

export enum AssessmentCategory {
  CONTINUOUS = 'continuous',
  FORMATIVE = 'formative',
  SUMMATIVE = 'summative',
  FINAL = 'final'
}

export enum TermNumber {
  TERM_1 = 1,
  TERM_2 = 2,
  TERM_3 = 3
}

export enum SessionType {
  REGULAR = 'regular',
  MAKEUP = 'makeup',
  EXTRA = 'extra',
  EXAM = 'exam'
}

export enum EventType {
  HOLIDAY = 'holiday',
  EXAM = 'exam',
  ASSESSMENT = 'assessment',
  SPORTS = 'sports',
  CULTURAL = 'cultural',
  MEETING = 'meeting',
  TRAINING = 'training',
  OTHER = 'other'
}

// Subject interfaces
export interface Subject {
  id: string
  school_id: string
  code: string
  name: string
  description?: string
  grade_levels: number[]
  is_core: boolean
  is_practical: boolean
  requires_lab: boolean
  pass_mark: number
  max_mark: number
  credit_hours: number
  department?: string
  language_of_instruction: string
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface SubjectCreate {
  code: string
  name: string
  description?: string
  grade_levels: number[]
  is_core?: boolean
  is_practical?: boolean
  requires_lab?: boolean
  pass_mark?: number
  max_mark?: number
  credit_hours?: number
  department?: string
  language_of_instruction?: string
  display_order?: number
}

export interface SubjectUpdate {
  code?: string
  name?: string
  description?: string
  grade_levels?: number[]
  is_core?: boolean
  is_practical?: boolean
  requires_lab?: boolean
  pass_mark?: number
  max_mark?: number
  credit_hours?: number
  department?: string
  language_of_instruction?: string
  display_order?: number
  is_active?: boolean
}

// Curriculum interfaces
export interface Curriculum {
  id: string
  school_id: string
  academic_year_id: string
  name: string
  description?: string
  grade_level: number
  term_number?: TermNumber
  subject_id: string
  learning_objectives: string[]
  learning_outcomes: string[]
  assessment_methods: string[]
  resources_required: string[]
  total_periods: number
  practical_periods: number
  effective_from: string
  effective_to?: string
  status: string
  approved_by?: string
  approved_at?: string
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface CurriculumCreate {
  academic_year_id: string
  name: string
  description?: string
  grade_level: number
  term_number?: TermNumber
  subject_id: string
  learning_objectives?: string[]
  learning_outcomes?: string[]
  assessment_methods?: string[]
  resources_required?: string[]
  total_periods?: number
  practical_periods?: number
  effective_from: string
  effective_to?: string
}

// Period interfaces
export interface Period {
  id: string
  school_id: string
  period_number: number
  name: string
  start_time: string
  end_time: string
  is_break: boolean
  break_type?: string
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface PeriodCreate {
  period_number: number
  name: string
  start_time: string
  end_time: string
  is_break?: boolean
  break_type?: string
}

// Timetable interfaces
export interface Timetable {
  id: string
  school_id: string
  academic_year_id: string
  term_number: number
  class_id: string
  subject_id: string
  teacher_id: string
  period_id: string
  day_of_week: number
  room_number?: string
  is_double_period: boolean
  is_practical: boolean
  week_pattern: string
  effective_from: string
  effective_to?: string
  notes?: string
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface TimetableWithDetails extends Timetable {
  subject_name: string
  teacher_name: string
  period_name: string
  class_name: string
  start_time: string
  end_time: string
}

export interface TimetableCreate {
  academic_year_id: string
  term_number: TermNumber
  class_id: string
  subject_id: string
  teacher_id: string
  period_id: string
  day_of_week: number
  room_number?: string
  is_double_period?: boolean
  is_practical?: boolean
  week_pattern?: string
  effective_from: string
  effective_to?: string
  notes?: string
}

// Attendance interfaces
export interface AttendanceSession {
  id: string
  school_id: string
  timetable_id: string
  period_id: string
  teacher_id: string
  subject_id: string
  class_id: string
  session_date: string
  session_type: SessionType
  session_status: string
  attendance_marked: boolean
  marked_by?: string
  marked_at?: string
  total_students: number
  present_students: number
  absent_students: number
  late_students: number
  notes?: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface AttendanceRecord {
  id: string
  school_id: string
  attendance_session_id: string
  student_id: string
  attendance_status: AttendanceStatus
  arrival_time?: string
  departure_time?: string
  excuse_reason?: string
  is_excused: boolean
  notes?: string
  marked_by: string
  marked_at: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface AttendanceRecordCreate {
  student_id: string
  attendance_status: AttendanceStatus
  arrival_time?: string
  departure_time?: string
  excuse_reason?: string
  is_excused?: boolean
  notes?: string
}

export interface BulkAttendanceCreate {
  attendance_session_id: string
  attendance_records: AttendanceRecordCreate[]
}

export interface AttendanceStats {
  total_students: number
  present_students: number
  absent_students: number
  late_students: number
  attendance_rate: number
}

// Assessment interfaces
export interface Assessment {
  id: string
  school_id: string
  academic_year_id: string
  name: string
  description?: string
  subject_id: string
  class_id: string
  teacher_id: string
  term_number: TermNumber
  assessment_type: AssessmentType
  assessment_category: AssessmentCategory
  total_marks: number
  pass_mark: number
  weight_percentage: number
  assessment_date: string
  due_date?: string
  duration_minutes?: number
  instructions?: string
  resources_allowed: string[]
  is_group_assessment: boolean
  max_group_size?: number
  status: string
  published_at?: string
  published_by?: string
  results_published: boolean
  results_published_at?: string
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface AssessmentCreate {
  academic_year_id: string
  name: string
  description?: string
  subject_id: string
  class_id: string
  teacher_id: string
  term_number: TermNumber
  assessment_type: AssessmentType
  assessment_category?: AssessmentCategory
  total_marks?: number
  pass_mark?: number
  weight_percentage?: number
  assessment_date: string
  due_date?: string
  duration_minutes?: number
  instructions?: string
  resources_allowed?: string[]
  is_group_assessment?: boolean
  max_group_size?: number
}

// Grade interfaces
export interface Grade {
  id: string
  school_id: string
  assessment_id: string
  student_id: string
  raw_score?: number
  percentage_score?: number
  letter_grade?: GradingScale
  grade_points?: number
  is_absent: boolean
  is_excused: boolean
  submission_date?: string
  feedback?: string
  improvement_suggestions?: string
  next_steps?: string
  graded_by: string
  graded_at: string
  parent_viewed: boolean
  parent_viewed_at?: string
  is_final: boolean
  moderated_by?: string
  moderated_at?: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by?: string
}

export interface GradeCreate {
  assessment_id: string
  student_id: string
  raw_score?: number
  percentage_score?: number
  letter_grade?: GradingScale
  grade_points?: number
  is_absent?: boolean
  is_excused?: boolean
  submission_date?: string
  feedback?: string
  improvement_suggestions?: string
  next_steps?: string
}

export interface BulkGradeCreate {
  assessment_id: string
  grades: GradeCreate[]
}

// Dashboard interfaces
export interface AcademicDashboard {
  school_id: string
  academic_year_id: string
  total_subjects: number
  total_classes: number
  total_teachers: number
  total_students: number
  average_attendance_rate: number
  total_assessments: number
  completed_assessments: number
  pending_assessments: number
  recent_grades: any[]
  upcoming_events: any[]
  attendance_trend: any[]
  grade_distribution: any[]
  subject_performance: any[]
}

export interface TeacherDashboard {
  teacher_id: string
  school_id: string
  academic_year_id: string
  total_classes: number
  total_subjects: number
  total_students: number
  my_attendance_rate: number
  pending_assessments: number
  recent_lesson_plans: any[]
  upcoming_sessions: any[]
  grade_summary: any[]
}

// Response interfaces
export interface PaginatedResponse<T> {
  items: T[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface BulkOperationResponse {
  total_processed: number
  successful: number
  failed: number
  errors: any[]
  created_ids: string[]
}

// Filter interfaces
export interface SubjectFilters {
  grade_level?: number
  department?: string
  is_core?: boolean
  page?: number
  page_size?: number
}

export interface CurriculumFilters {
  academic_year_id?: string
  grade_level?: number
  subject_id?: string
  term_number?: number
  page?: number
  page_size?: number
}

export interface AttendanceStatsFilters {
  class_id?: string
  subject_id?: string
  start_date?: string
  end_date?: string
}

// =====================================================
// API CLIENT
// =====================================================

class AcademicApi {
  private api: ApiClient

  constructor() {
    this.api = new ApiClient()
  }

  // =====================================================
  // SUBJECT ENDPOINTS
  // =====================================================

  async getSubjects(filters: SubjectFilters = {}): Promise<PaginatedResponse<Subject>> {
    const params = new URLSearchParams()
    
    if (filters.grade_level) params.append('grade_level', filters.grade_level.toString())
    if (filters.department) params.append('department', filters.department)
    if (filters.is_core !== undefined) params.append('is_core', filters.is_core.toString())
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.page_size) params.append('page_size', filters.page_size.toString())

    return this.api.get(`/academic/subjects?${params}`)
  }

  async getSubject(id: string): Promise<Subject> {
    return this.api.get(`/academic/subjects/${id}`)
  }

  async createSubject(data: SubjectCreate): Promise<Subject> {
    return this.api.post('/academic/subjects', data)
  }

  async updateSubject(id: string, data: SubjectUpdate): Promise<Subject> {
    return this.api.put(`/academic/subjects/${id}`, data)
  }

  async deleteSubject(id: string): Promise<void> {
    return this.api.delete(`/academic/subjects/${id}`)
  }

  // =====================================================
  // CURRICULUM ENDPOINTS
  // =====================================================

  async getCurricula(filters: CurriculumFilters = {}): Promise<PaginatedResponse<Curriculum>> {
    const params = new URLSearchParams()
    
    if (filters.academic_year_id) params.append('academic_year_id', filters.academic_year_id)
    if (filters.grade_level) params.append('grade_level', filters.grade_level.toString())
    if (filters.subject_id) params.append('subject_id', filters.subject_id)
    if (filters.term_number) params.append('term_number', filters.term_number.toString())
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.page_size) params.append('page_size', filters.page_size.toString())

    return this.api.get(`/academic/curriculum?${params}`)
  }

  async getCurriculum(id: string): Promise<Curriculum> {
    return this.api.get(`/academic/curriculum/${id}`)
  }

  async createCurriculum(data: CurriculumCreate): Promise<Curriculum> {
    return this.api.post('/academic/curriculum', data)
  }

  // =====================================================
  // TIMETABLE ENDPOINTS
  // =====================================================

  async createPeriod(data: PeriodCreate): Promise<Period> {
    return this.api.post('/academic/periods', data)
  }

  async createTimetableEntry(data: TimetableCreate): Promise<Timetable> {
    return this.api.post('/academic/timetables', data)
  }

  // =====================================================
  // ATTENDANCE ENDPOINTS
  // =====================================================

  async createAttendanceSession(data: { timetable_id: string; session_date: string; session_type?: SessionType; notes?: string }): Promise<AttendanceSession> {
    return this.api.post('/academic/attendance/sessions', data)
  }

  async markBulkAttendance(data: BulkAttendanceCreate): Promise<BulkOperationResponse> {
    return this.api.post('/academic/attendance/bulk', data)
  }

  async getAttendanceStats(filters: AttendanceStatsFilters = {}): Promise<AttendanceStats> {
    const params = new URLSearchParams()
    
    if (filters.class_id) params.append('class_id', filters.class_id)
    if (filters.subject_id) params.append('subject_id', filters.subject_id)
    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)

    return this.api.get(`/academic/attendance/stats?${params}`)
  }

  // =====================================================
  // ASSESSMENT ENDPOINTS
  // =====================================================

  async createAssessment(data: AssessmentCreate): Promise<Assessment> {
    return this.api.post('/academic/assessments', data)
  }

  async submitBulkGrades(assessmentId: string, data: BulkGradeCreate): Promise<BulkOperationResponse> {
    return this.api.post(`/academic/assessments/${assessmentId}/grades/bulk`, data)
  }

  // =====================================================
  // DASHBOARD ENDPOINTS
  // =====================================================

  async getAcademicDashboard(academicYearId: string): Promise<AcademicDashboard> {
    return this.api.get(`/academic/dashboard?academic_year_id=${academicYearId}`)
  }

  async getTeacherDashboard(academicYearId: string, teacherId?: string): Promise<TeacherDashboard> {
    const params = new URLSearchParams({ academic_year_id: academicYearId })
    if (teacherId) params.append('teacher_id', teacherId)
    
    return this.api.get(`/academic/dashboard/teacher?${params}`)
  }

  // =====================================================
  // UTILITY ENDPOINTS
  // =====================================================

  async getTermsEnum(): Promise<Array<{ value: number; label: string; description: string }>> {
    return this.api.get('/academic/enums/terms')
  }

  async getAssessmentTypesEnum(): Promise<Array<{ value: string; label: string }>> {
    return this.api.get('/academic/enums/assessment-types')
  }

  async getAttendanceStatusesEnum(): Promise<Array<{ value: string; label: string }>> {
    return this.api.get('/academic/enums/attendance-statuses')
  }

  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.api.get('/academic/health')
  }
}

export const academicApi = new AcademicApi()
export default academicApi