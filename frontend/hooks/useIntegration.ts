/**
 * Integration Hooks
 * React hooks for cross-module integration functionality
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { toast } from 'sonner'

import integrationApi, {
  StudentPerformance,
  AttendanceStats,
  StudentWithDetails,
  ClassAcademicSummary,
  SubjectAccessInfo,
  AssessmentAccessInfo,
  InvoiceCreationResult,
  ResourceUsageBilling,
  AcademicFinancialSummary,
  PaymentRestriction,
  Guardian,
  ClassEnrollmentSync
} from '@/lib/integration-api'

// =====================================================
// ACADEMIC-SIS INTEGRATION HOOKS
// =====================================================

export function useClassStudentsForAcademic(
  classId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'class-students-academic', classId, academicYearId],
    queryFn: () => integrationApi.getClassStudentsForAcademic(classId!, academicYearId!),
    enabled: Boolean(classId && academicYearId) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useStudentAcademicPerformance(
  studentId: string | undefined,
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'student-performance', studentId, academicYearId, termNumber],
    queryFn: () => integrationApi.getStudentAcademicPerformance(studentId!, academicYearId!, termNumber),
    enabled: Boolean(studentId && academicYearId) && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useStudentAttendanceStats(
  studentId: string | undefined,
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'student-attendance', studentId, academicYearId, termNumber],
    queryFn: () => integrationApi.getStudentAttendanceStats(studentId!, academicYearId!, termNumber),
    enabled: Boolean(studentId && academicYearId) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useClassAcademicSummary(
  classId: string | undefined,
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'class-summary', classId, academicYearId, termNumber],
    queryFn: () => integrationApi.getClassAcademicSummary(classId!, academicYearId!, termNumber),
    enabled: Boolean(classId && academicYearId) && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useStudentGuardiansForNotifications(
  studentId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'student-guardians', studentId],
    queryFn: () => integrationApi.getStudentGuardiansForNotifications(studentId!),
    enabled: Boolean(studentId) && (options?.enabled ?? true),
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

// =====================================================
// ACADEMIC-FINANCE INTEGRATION HOOKS
// =====================================================

export function useStudentSubjectAccess(
  studentId: string | undefined,
  subjectId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'subject-access', studentId, subjectId, academicYearId],
    queryFn: () => integrationApi.checkStudentSubjectAccess(studentId!, subjectId!, academicYearId!),
    enabled: Boolean(studentId && subjectId && academicYearId) && (options?.enabled ?? true),
    staleTime: 2 * 60 * 1000, // 2 minutes - shorter for payment-related data
  })
}

export function useStudentAssessmentAccess(
  studentId: string | undefined,
  assessmentId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'assessment-access', studentId, assessmentId],
    queryFn: () => integrationApi.checkStudentAssessmentAccess(studentId!, assessmentId!),
    enabled: Boolean(studentId && assessmentId) && (options?.enabled ?? true),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useAcademicFinancialSummary(
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'academic-financial-summary', academicYearId, termNumber],
    queryFn: () => integrationApi.getAcademicFinancialSummary(academicYearId!, termNumber),
    enabled: Boolean(academicYearId) && (options?.enabled ?? true),
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

export function useStudentsWithPaymentRestrictions(
  classId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'payment-restrictions', classId, academicYearId],
    queryFn: () => integrationApi.getStudentsWithPaymentRestrictions(classId!, academicYearId!),
    enabled: Boolean(classId && academicYearId) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// =====================================================
// MUTATION HOOKS
// =====================================================

export function useGenerateSubjectEnrollmentInvoice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ studentId, subjectId, academicYearId }: {
      studentId: string
      subjectId: string
      academicYearId: string
    }) => integrationApi.generateSubjectEnrollmentInvoice(studentId, subjectId, academicYearId),
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['integration', 'subject-access'] })
      queryClient.invalidateQueries({ queryKey: ['finance', 'invoices'] })
      toast.success(`Generated ${data.invoices_created.length} invoice(s) for subject enrollment`)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate enrollment invoice')
    }
  })
}

export function useProcessResourceUsageBilling() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      student_id: string
      resource_type: string
      resource_id: string
      usage_amount: number
      academic_year_id: string
    }) => integrationApi.processResourceUsageBilling(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'subject-access'] })
      queryClient.invalidateQueries({ queryKey: ['finance', 'invoices'] })
      toast.success(`Billed $${data.total_cost.toFixed(2)} for ${data.resource_type} usage`)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to process resource usage billing')
    }
  })
}

export function useSyncClassEnrollmentWithAcademic() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ classId, academicYearId }: {
      classId: string
      academicYearId: string
    }) => integrationApi.syncClassEnrollmentWithAcademic(classId, academicYearId),
    onSuccess: (data) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: ['integration', 'class-students-academic'] })
      queryClient.invalidateQueries({ queryKey: ['integration', 'class-summary'] })
      queryClient.invalidateQueries({ queryKey: ['sis', 'enrollments'] })
      toast.success(`Synced ${data.students.length} students with academic system`)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to sync class enrollment')
    }
  })
}

// =====================================================
// VALIDATION HOOKS
// =====================================================

export function useValidateStudentEnrollment(
  studentId: string | undefined,
  classId: string | undefined,
  subjectId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'validate-enrollment', studentId, classId, subjectId, academicYearId],
    queryFn: () => integrationApi.validateStudentEnrollmentForAcademic(
      studentId!, classId!, subjectId!, academicYearId!
    ),
    enabled: Boolean(studentId && classId && subjectId && academicYearId) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useValidateStudentAcademicAccess(
  studentId: string | undefined,
  subjectId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'validate-access', studentId, subjectId, academicYearId],
    queryFn: () => integrationApi.validateStudentAcademicAccess(studentId!, subjectId!, academicYearId!),
    enabled: Boolean(studentId && subjectId && academicYearId) && (options?.enabled ?? true),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// =====================================================
// COMPOSITE HOOKS
// =====================================================

export function useStudentFullAcademicProfile(
  studentId: string | undefined,
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'student-full-profile', studentId, academicYearId, termNumber],
    queryFn: () => integrationApi.getStudentFullAcademicProfile(studentId!, academicYearId!, termNumber),
    enabled: Boolean(studentId && academicYearId) && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useClassFullAcademicProfile(
  classId: string | undefined,
  academicYearId: string | undefined,
  termNumber?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'class-full-profile', classId, academicYearId, termNumber],
    queryFn: () => integrationApi.getClassFullAcademicProfile(classId!, academicYearId!, termNumber),
    enabled: Boolean(classId && academicYearId) && (options?.enabled ?? true),
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

// =====================================================
// BATCH OPERATIONS HOOKS
// =====================================================

export function useMultipleStudentsSubjectAccess(
  studentIds: string[],
  subjectId: string | undefined,
  academicYearId: string | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['integration', 'multiple-subject-access', studentIds, subjectId, academicYearId],
    queryFn: () => integrationApi.checkMultipleStudentsSubjectAccess(studentIds, subjectId!, academicYearId!),
    enabled: Boolean(studentIds.length > 0 && subjectId && academicYearId) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// =====================================================
// UTILITY HOOKS
// =====================================================

export function useIntegrationHealthCheck() {
  return useQuery({
    queryKey: ['integration', 'health'],
    queryFn: () => integrationApi.healthCheck(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// =====================================================
// CUSTOM HOOKS FOR SPECIFIC USE CASES
// =====================================================

export function useStudentAccessChecker() {
  const generateInvoiceMutation = useGenerateSubjectEnrollmentInvoice()

  const checkAndEnrollStudent = useCallback(async (
    studentId: string,
    subjectId: string,
    academicYearId: string
  ) => {
    try {
      // First check access
      const accessInfo = await integrationApi.checkStudentSubjectAccess(studentId, subjectId, academicYearId)
      
      if (!accessInfo.has_access) {
        // Generate invoice if needed
        if (accessInfo.required_fees.length > 0) {
          await generateInvoiceMutation.mutateAsync({ studentId, subjectId, academicYearId })
          return {
            success: false,
            reason: 'invoice_generated',
            message: 'Invoice generated for required fees. Student can access after payment.'
          }
        } else {
          return {
            success: false,
            reason: 'access_denied',
            message: accessInfo.reason || 'Access denied'
          }
        }
      }
      
      return {
        success: true,
        message: 'Student has access to subject'
      }
    } catch (error) {
      return {
        success: false,
        reason: 'error',
        message: 'Failed to check student access'
      }
    }
  }, [generateInvoiceMutation])

  return {
    checkAndEnrollStudent,
    isLoading: generateInvoiceMutation.isPending
  }
}

export function useClassPaymentMonitor(
  classId: string | undefined,
  academicYearId: string | undefined
) {
  const { data: restrictions, isLoading } = useStudentsWithPaymentRestrictions(
    classId,
    academicYearId
  )

  const getRestrictionSummary = useCallback(() => {
    if (!restrictions) return null

    const total = restrictions.length
    const high = restrictions.filter(r => r.restriction_level === 'high').length
    const medium = restrictions.filter(r => r.restriction_level === 'medium').length
    const totalOutstanding = restrictions.reduce((sum, r) => sum + r.total_outstanding, 0)

    return {
      total,
      high,
      medium,
      totalOutstanding,
      hasRestrictions: total > 0
    }
  }, [restrictions])

  return {
    restrictions: restrictions || [],
    summary: getRestrictionSummary(),
    isLoading
  }
}

export default {
  // Academic-SIS hooks
  useClassStudentsForAcademic,
  useStudentAcademicPerformance,
  useStudentAttendanceStats,
  useClassAcademicSummary,
  useStudentGuardiansForNotifications,
  
  // Academic-Finance hooks
  useStudentSubjectAccess,
  useStudentAssessmentAccess,
  useAcademicFinancialSummary,
  useStudentsWithPaymentRestrictions,
  
  // Mutation hooks
  useGenerateSubjectEnrollmentInvoice,
  useProcessResourceUsageBilling,
  useSyncClassEnrollmentWithAcademic,
  
  // Validation hooks
  useValidateStudentEnrollment,
  useValidateStudentAcademicAccess,
  
  // Composite hooks
  useStudentFullAcademicProfile,
  useClassFullAcademicProfile,
  useMultipleStudentsSubjectAccess,
  
  // Utility hooks
  useIntegrationHealthCheck,
  useStudentAccessChecker,
  useClassPaymentMonitor
}