/**
 * Integration API Client
 * Cross-module integration between Academic, SIS, and Finance
 */

import { ApiClient } from './api'

// =====================================================
// TYPES AND INTERFACES
// =====================================================

export interface StudentPerformance {
  student_id: string
  student_name: string
  grade_level: number
  class_name: string
  overall_average: number
  attendance_rate: number
  subject_grades: SubjectGrade[]
  recent_assessments: RecentAssessment[]
  strengths: string[]
  areas_for_improvement: string[]
}

export interface SubjectGrade {
  subject_id: string
  subject_name: string
  grades: GradeRecord[]
  average: number
  latest_grade?: GradeRecord
}

export interface GradeRecord {
  assessment_name: string
  assessment_type: string
  percentage_score: number
  letter_grade: string
  assessment_date: string
  feedback?: string
}

export interface RecentAssessment {
  assessment_name: string
  subject_name: string
  assessment_type: string
  percentage_score: number
  letter_grade: string
  assessment_date: string
}

export interface AttendanceStats {
  total_students: number
  present_students: number
  absent_students: number
  late_students: number
  attendance_rate: number
}

export interface StudentWithDetails {
  id: string
  school_id: string
  student_number: string
  first_name: string
  last_name: string
  middle_names?: string
  preferred_name?: string
  date_of_birth: string
  gender: string
  nationality: string
  national_id?: string
  birth_certificate_number?: string
  phone_number?: string
  email_address?: string
  physical_address?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  medical_conditions?: string[]
  dietary_requirements?: string[]
  transport_method?: string
  previous_school?: string
  enrollment_date?: string
  grade_level?: number
  class_id?: string
  guardians: Guardian[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Guardian {
  id: string
  name: string
  relationship: string
  phone_number?: string
  email_address?: string
  preferred_contact_method: string
  notification_preferences: Record<string, any>
}

export interface ClassAcademicSummary {
  class_id: string
  class_name: string
  grade_level: number
  total_students: number
  total_assessments: number
  completed_assessments: number
  class_average: number
  total_grades: number
  attendance_rate: number
  teacher_id?: string
  academic_year_id: string
  term_number?: number
}

export interface SubjectAccessInfo {
  has_access: boolean
  reason?: string
  outstanding_balance: number
  required_fees: FeeInfo[]
  subject_fees: FeeInfo[]
}

export interface AssessmentAccessInfo {
  has_access: boolean
  assessment_name: string
  subject_name: string
  subject_access: SubjectAccessInfo
  exam_fees_outstanding: FeeInfo[]
  total_outstanding: number
}

export interface FeeInfo {
  fee_category_id: string
  fee_name: string
  amount: number
  due_date?: string
  invoice_id?: string
  description?: string
}

export interface InvoiceCreationResult {
  student_id: string
  subject_id: string
  subject_name: string
  invoices_created: CreatedInvoice[]
  total_amount: number
}

export interface CreatedInvoice {
  invoice_id: string
  fee_category_name: string
  amount: number
  due_date: string
  description: string
}

export interface ResourceUsageBilling {
  invoice_id: string
  resource_type: string
  usage_amount: number
  unit_cost: number
  total_cost: number
  due_date: string
}

export interface AcademicFinancialSummary {
  school_id: string
  academic_year_id: string
  term_number?: number
  summary: FinancialSummaryStats
  fee_breakdown: FeeBreakdown[]
  generated_at: string
}

export interface FinancialSummaryStats {
  total_invoices: number
  total_invoiced: number
  total_paid: number
  total_outstanding: number
  collection_rate: number
  total_payments: number
  total_payment_amount: number
}

export interface FeeBreakdown {
  fee_category_id: string
  fee_name: string
  fee_type: string
  total_invoices: number
  total_amount: number
  paid_amount: number
  outstanding_amount: number
}

export interface PaymentRestriction {
  student_id: string
  total_outstanding: number
  outstanding_invoices: number
  restrictions: string[]
  restriction_level: 'high' | 'medium' | 'low'
}

export interface EnrollmentValidation {
  is_valid: boolean
}

export interface AccessValidation {
  has_access: boolean
}

export interface ClassEnrollmentSync {
  students: StudentWithDetails[]
  summary: ClassAcademicSummary
  sync_timestamp: string
}

// =====================================================
// API CLIENT
// =====================================================

class IntegrationApi {
  private api: ApiClient

  constructor() {
    this.api = new ApiClient()
  }

  // =====================================================
  // ACADEMIC-SIS INTEGRATION
  // =====================================================

  async getClassStudentsForAcademic(
    classId: string, 
    academicYearId: string
  ): Promise<StudentWithDetails[]> {
    return this.api.get(`/integration/academic/class/${classId}/students?academic_year_id=${academicYearId}`)
  }

  async getStudentAcademicPerformance(
    studentId: string,
    academicYearId: string,
    termNumber?: number
  ): Promise<StudentPerformance> {
    const params = new URLSearchParams({ academic_year_id: academicYearId })
    if (termNumber) params.append('term_number', termNumber.toString())
    
    return this.api.get(`/integration/academic/student/${studentId}/performance?${params}`)
  }

  async getStudentAttendanceStats(
    studentId: string,
    academicYearId: string,
    termNumber?: number
  ): Promise<AttendanceStats> {
    const params = new URLSearchParams({ academic_year_id: academicYearId })
    if (termNumber) params.append('term_number', termNumber.toString())
    
    return this.api.get(`/integration/academic/student/${studentId}/attendance?${params}`)
  }

  async getClassAcademicSummary(
    classId: string,
    academicYearId: string,
    termNumber?: number
  ): Promise<ClassAcademicSummary> {
    const params = new URLSearchParams({ academic_year_id: academicYearId })
    if (termNumber) params.append('term_number', termNumber.toString())
    
    return this.api.get(`/integration/academic/class/${classId}/summary?${params}`)
  }

  async getStudentGuardiansForNotifications(studentId: string): Promise<Guardian[]> {
    return this.api.get(`/integration/academic/student/${studentId}/guardians`)
  }

  // =====================================================
  // ACADEMIC-FINANCE INTEGRATION
  // =====================================================

  async checkStudentSubjectAccess(
    studentId: string,
    subjectId: string,
    academicYearId: string
  ): Promise<SubjectAccessInfo> {
    return this.api.get(
      `/integration/finance/student/${studentId}/subject/${subjectId}/access?academic_year_id=${academicYearId}`
    )
  }

  async checkStudentAssessmentAccess(
    studentId: string,
    assessmentId: string
  ): Promise<AssessmentAccessInfo> {
    return this.api.get(`/integration/finance/student/${studentId}/assessment/${assessmentId}/access`)
  }

  async generateSubjectEnrollmentInvoice(
    studentId: string,
    subjectId: string,
    academicYearId: string
  ): Promise<InvoiceCreationResult> {
    return this.api.post(
      `/integration/finance/student/${studentId}/subject/${subjectId}/invoice?academic_year_id=${academicYearId}`,
      {}
    )
  }

  async processResourceUsageBilling(data: {
    student_id: string
    resource_type: string
    resource_id: string
    usage_amount: number
    academic_year_id: string
  }): Promise<ResourceUsageBilling> {
    const params = new URLSearchParams({ academic_year_id: data.academic_year_id })
    
    return this.api.post(`/integration/finance/resource-usage?${params}`, {
      student_id: data.student_id,
      resource_type: data.resource_type,
      resource_id: data.resource_id,
      usage_amount: data.usage_amount
    })
  }

  async getAcademicFinancialSummary(
    academicYearId: string,
    termNumber?: number
  ): Promise<AcademicFinancialSummary> {
    const params = new URLSearchParams({ academic_year_id: academicYearId })
    if (termNumber) params.append('term_number', termNumber.toString())
    
    return this.api.get(`/integration/finance/academic/summary?${params}`)
  }

  async getStudentsWithPaymentRestrictions(
    classId: string,
    academicYearId: string
  ): Promise<PaymentRestriction[]> {
    return this.api.get(
      `/integration/finance/class/${classId}/payment-restrictions?academic_year_id=${academicYearId}`
    )
  }

  // =====================================================
  // VALIDATION ENDPOINTS
  // =====================================================

  async validateStudentEnrollmentForAcademic(
    studentId: string,
    classId: string,
    subjectId: string,
    academicYearId: string
  ): Promise<EnrollmentValidation> {
    const params = new URLSearchParams({
      class_id: classId,
      subject_id: subjectId,
      academic_year_id: academicYearId
    })
    
    return this.api.get(`/integration/validate/student/${studentId}/enrollment?${params}`)
  }

  async validateStudentAcademicAccess(
    studentId: string,
    subjectId: string,
    academicYearId: string
  ): Promise<AccessValidation> {
    const params = new URLSearchParams({
      subject_id: subjectId,
      academic_year_id: academicYearId
    })
    
    return this.api.get(`/integration/validate/student/${studentId}/academic-access?${params}`)
  }

  // =====================================================
  // BULK OPERATIONS
  // =====================================================

  async syncClassEnrollmentWithAcademic(
    classId: string,
    academicYearId: string
  ): Promise<ClassEnrollmentSync> {
    return this.api.post(
      `/integration/sync/class/${classId}/enrollment-academic?academic_year_id=${academicYearId}`,
      {}
    )
  }

  // =====================================================
  // UTILITY METHODS
  // =====================================================

  async checkMultipleStudentsSubjectAccess(
    studentIds: string[],
    subjectId: string,
    academicYearId: string
  ): Promise<Record<string, SubjectAccessInfo>> {
    const results: Record<string, SubjectAccessInfo> = {}
    
    // Execute in parallel but limit concurrency to avoid overwhelming the server
    const batchSize = 5
    for (let i = 0; i < studentIds.length; i += batchSize) {
      const batch = studentIds.slice(i, i + batchSize)
      const batchPromises = batch.map(async (studentId) => {
        try {
          const access = await this.checkStudentSubjectAccess(studentId, subjectId, academicYearId)
          return { studentId, access }
        } catch (error) {
          console.error(`Failed to check access for student ${studentId}:`, error)
          return {
            studentId,
            access: {
              has_access: false,
              reason: 'Error checking access',
              outstanding_balance: 0,
              required_fees: [],
              subject_fees: []
            }
          }
        }
      })
      
      const batchResults = await Promise.all(batchPromises)
      batchResults.forEach(({ studentId, access }) => {
        results[studentId] = access
      })
    }
    
    return results
  }

  async getStudentFullAcademicProfile(
    studentId: string,
    academicYearId: string,
    termNumber?: number
  ): Promise<{
    performance: StudentPerformance
    attendance: AttendanceStats
    guardians: Guardian[]
  }> {
    const [performance, attendance, guardians] = await Promise.all([
      this.getStudentAcademicPerformance(studentId, academicYearId, termNumber),
      this.getStudentAttendanceStats(studentId, academicYearId, termNumber),
      this.getStudentGuardiansForNotifications(studentId)
    ])

    return {
      performance,
      attendance,
      guardians
    }
  }

  async getClassFullAcademicProfile(
    classId: string,
    academicYearId: string,
    termNumber?: number
  ): Promise<{
    students: StudentWithDetails[]
    summary: ClassAcademicSummary
    payment_restrictions: PaymentRestriction[]
    financial_summary: AcademicFinancialSummary
  }> {
    const [students, summary, paymentRestrictions, financialSummary] = await Promise.all([
      this.getClassStudentsForAcademic(classId, academicYearId),
      this.getClassAcademicSummary(classId, academicYearId, termNumber),
      this.getStudentsWithPaymentRestrictions(classId, academicYearId),
      this.getAcademicFinancialSummary(academicYearId, termNumber)
    ])

    return {
      students,
      summary,
      payment_restrictions: paymentRestrictions,
      financial_summary: financialSummary
    }
  }

  // =====================================================
  // HEALTH CHECK
  // =====================================================

  async healthCheck(): Promise<{ status: string; service: string; modules: string[]; timestamp: string }> {
    return this.api.get('/integration/health')
  }
}

export const integrationApi = new IntegrationApi()
export default integrationApi