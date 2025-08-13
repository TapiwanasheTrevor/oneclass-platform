// =====================================================
// SIS Module API Integration
// File: frontend/lib/sis-api.ts
// =====================================================

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import { toast } from 'sonner'

// =====================================================
// TYPES & INTERFACES
// =====================================================

export interface ZimbabweAddress {
  street: string
  suburb: string
  city: string
  province: string
  postal_code?: string
}

export interface EmergencyContact {
  name: string
  relationship: string
  phone: string
  alternative_phone?: string
  is_primary: boolean
  can_pickup: boolean
  address?: string
}

export interface MedicalCondition {
  condition: string
  severity: 'Mild' | 'Moderate' | 'Severe'
  medication?: string
  notes?: string
  diagnosed_date?: string
  doctor_name?: string
}

export interface Allergy {
  allergen: string
  reaction: string
  severity: 'Mild' | 'Moderate' | 'Severe' | 'Life-threatening'
  epipen_required: boolean
  treatment?: string
}

export interface StudentCreate {
  // Personal Information
  first_name: string
  middle_name?: string
  last_name: string
  preferred_name?: string
  date_of_birth: string
  gender: 'Male' | 'Female' | 'Other'
  nationality: string
  home_language?: 'English' | 'Shona' | 'Ndebele' | 'Tonga' | 'Kalanga' | 'Nambya' | 'Other'
  religion?: string
  tribe?: string
  
  // Contact Information
  mobile_number?: string
  email?: string
  residential_address: ZimbabweAddress
  postal_address?: ZimbabweAddress
  
  // Academic Information
  current_grade_level: number
  current_class_id?: string
  enrollment_date: string
  previous_school_name?: string
  transfer_reason?: string
  
  // Medical Information
  blood_type?: 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-'
  medical_conditions: MedicalCondition[]
  allergies: Allergy[]
  medical_aid_provider?: string
  medical_aid_number?: string
  special_needs?: Record<string, any>
  dietary_requirements?: string
  
  // Emergency Contacts
  emergency_contacts: EmergencyContact[]
  
  // Additional Information
  transport_needs?: string
  identifying_marks?: string
}

export interface Student {
  id: string
  school_id: string
  user_id?: string
  student_number: string
  zimsec_number?: string
  
  // Personal Information
  first_name: string
  middle_name?: string
  last_name: string
  preferred_name?: string
  full_name: string
  date_of_birth: string
  age: number
  gender: 'Male' | 'Female' | 'Other'
  nationality: string
  home_language?: string
  religion?: string
  tribe?: string
  
  // Contact Information
  mobile_number?: string
  email?: string
  residential_address: Record<string, any>
  postal_address?: Record<string, any>
  
  // Academic Information
  current_grade_level?: number
  current_class_id?: string
  enrollment_date: string
  expected_graduation_date?: string
  status: 'active' | 'suspended' | 'transferred' | 'graduated' | 'expelled' | 'deceased'
  
  // Points and Behavior
  disciplinary_points: number
  merit_points: number
  
  // Medical Information (basic only for privacy)
  blood_type?: string
  medical_aid_provider?: string
  has_medical_conditions: boolean
  has_allergies: boolean
  special_needs?: Record<string, any>
  dietary_requirements?: string
  
  // System Information
  created_at: string
  updated_at: string
}

export interface StudentUpdate {
  first_name?: string
  middle_name?: string
  last_name?: string
  preferred_name?: string
  gender?: 'Male' | 'Female' | 'Other'
  home_language?: string
  religion?: string
  mobile_number?: string
  email?: string
  current_grade_level?: number
  current_class_id?: string
  status?: string
  residential_address?: ZimbabweAddress
  postal_address?: ZimbabweAddress
  medical_conditions?: MedicalCondition[]
  allergies?: Allergy[]
  emergency_contacts?: EmergencyContact[]
  special_needs?: Record<string, any>
  dietary_requirements?: string
  transport_needs?: string
}

export interface StudentSearchFilters {
  search_query?: string
  grade_level?: number
  class_id?: string
  status?: string
  gender?: string
  home_language?: string
  has_medical_conditions?: boolean
  has_special_needs?: boolean
  enrollment_year?: number
  age_min?: number
  age_max?: number
}

export interface StudentSearchRequest {
  search_query?: string
  filters?: StudentSearchFilters
  sort_by?: 'first_name' | 'last_name' | 'student_number' | 'enrollment_date' | 'grade_level'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface StudentSearchResponse {
  students: Student[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface GuardianRelationshipCreate {
  guardian_user_id: string
  relationship: string
  is_primary_contact: boolean
  is_emergency_contact: boolean
  contact_priority: number
  has_pickup_permission: boolean
  has_academic_access: boolean
  has_financial_responsibility: boolean
  financial_responsibility_percentage: number
  preferred_contact_method: 'email' | 'sms' | 'whatsapp' | 'call'
  alternative_phone?: string
  work_phone?: string
  employer?: string
  job_title?: string
}

export interface BulkImportResponse {
  import_id: string
  status: 'processing' | 'completed' | 'failed'
  message: string
}

export interface BulkImportStatus {
  import_id: string
  status: string
  total_records: number
  successful: number
  failed: number
  errors?: Array<{
    row: number
    error: string
    data: Record<string, any>
  }>
}

// =====================================================
// CONSTANTS
// =====================================================

export const ZIMBABWE_PROVINCES = [
  'Harare',
  'Bulawayo', 
  'Manicaland',
  'Mashonaland Central',
  'Mashonaland East',
  'Mashonaland West',
  'Masvingo',
  'Matabeleland North',
  'Matabeleland South',
  'Midlands'
] as const

export const HOME_LANGUAGES = [
  'English',
  'Shona',
  'Ndebele',
  'Tonga',
  'Kalanga',
  'Nambya',
  'Other'
] as const

export const BLOOD_TYPES = [
  'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
] as const

export const RELATIONSHIPS = [
  'Father',
  'Mother',
  'Guardian',
  'Grandmother', 
  'Grandfather',
  'Uncle',
  'Aunt',
  'Sister',
  'Brother',
  'Other'
] as const

// =====================================================
// API FUNCTIONS
// =====================================================

class SISApi {
  private baseUrl = '/api/v1/students'

  // Student CRUD Operations
  async createStudent(data: StudentCreate): Promise<Student> {
    const response = await api.post(this.baseUrl, data)
    return response.data
  }

  async getStudent(studentId: string): Promise<Student> {
    const response = await api.get(`${this.baseUrl}/${studentId}`)
    return response.data
  }

  async updateStudent(studentId: string, data: StudentUpdate): Promise<Student> {
    const response = await api.put(`${this.baseUrl}/${studentId}`, data)
    return response.data
  }

  async deleteStudent(studentId: string, softDelete = true): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`${this.baseUrl}/${studentId}?soft_delete=${softDelete}`)
    return response.data
  }

  async searchStudents(params: StudentSearchRequest = {}): Promise<StudentSearchResponse> {
    const response = await api.get(this.baseUrl, { params })
    return response.data
  }

  // Guardian Management
  async addGuardianRelationship(studentId: string, data: GuardianRelationshipCreate) {
    const response = await api.post(`${this.baseUrl}/${studentId}/guardians`, data)
    return response.data
  }

  async getStudentGuardians(studentId: string) {
    const response = await api.get(`${this.baseUrl}/${studentId}/guardians`)
    return response.data
  }

  // Bulk Operations
  async bulkImportStudents(file: File): Promise<BulkImportResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post(`${this.baseUrl}/bulk-import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  async getBulkImportStatus(importId: string): Promise<BulkImportStatus> {
    const response = await api.get(`${this.baseUrl}/bulk-import/${importId}/status`)
    return response.data
  }

  async exportStudents(params: {
    format: 'csv' | 'excel'
    grade_level?: number
    include_sensitive?: boolean
  }): Promise<Blob> {
    const response = await api.get(`${this.baseUrl}/export`, {
      params,
      responseType: 'blob'
    })
    return response.data
  }

  // Attendance Operations
  async markAttendance(studentId: string, data: {
    attendance_date: string
    period: string
    status: 'present' | 'absent' | 'late' | 'excused' | 'sick' | 'suspended'
    arrival_time?: string
    departure_time?: string
    absence_reason?: string
    excuse_provided?: boolean
    notes?: string
  }) {
    const response = await api.post(`${this.baseUrl}/${studentId}/attendance`, data)
    return response.data
  }

  async getStudentAttendance(studentId: string, params?: {
    start_date?: string
    end_date?: string
    period?: string
  }) {
    const response = await api.get(`${this.baseUrl}/${studentId}/attendance`, { params })
    return response.data
  }

  // Health Records
  async createHealthRecord(studentId: string, data: {
    record_type: 'checkup' | 'illness' | 'injury' | 'vaccination' | 'screening' | 'medication_change'
    record_date: string
    recorded_by: string
    symptoms?: string
    diagnosis?: string
    treatment_given?: string
    temperature_celsius?: number
    blood_pressure?: string
    pulse_rate?: number
    weight_kg?: number
    height_cm?: number
    recommendations?: string
    follow_up_required?: boolean
    follow_up_date?: string
    parent_contacted?: boolean
    sent_home?: boolean
  }) {
    const response = await api.post(`${this.baseUrl}/${studentId}/health-records`, data)
    return response.data
  }

  async getStudentHealthRecords(studentId: string) {
    const response = await api.get(`${this.baseUrl}/${studentId}/health-records`)
    return response.data
  }

  // Disciplinary Records
  async createDisciplinaryIncident(studentId: string, data: {
    incident_date: string
    incident_time?: string
    incident_type: string
    severity: 'minor' | 'moderate' | 'serious' | 'severe'
    description: string
    location?: string
    witnesses?: string
    action_taken: string
    points_deducted?: number
    suspension_days?: number
    detention_hours?: number
    counseling_required?: boolean
    parent_meeting_required?: boolean
    behavioral_contract_required?: boolean
  }) {
    const response = await api.post(`${this.baseUrl}/${studentId}/disciplinary`, data)
    return response.data
  }

  // Statistics
  async getStudentStats() {
    const response = await api.get(`${this.baseUrl}/stats`)
    return response.data
  }
}

export const sisApi = new SISApi()

// =====================================================
// REACT QUERY HOOKS
// =====================================================

export const useSISHooks = () => {
  const queryClient = useQueryClient()

  // Student Queries
  const useStudents = (params: StudentSearchRequest = {}) => {
    return useQuery({
      queryKey: ['students', params],
      queryFn: () => sisApi.searchStudents(params),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })
  }

  const useStudent = (studentId: string) => {
    return useQuery({
      queryKey: ['student', studentId],
      queryFn: () => sisApi.getStudent(studentId),
      enabled: !!studentId,
    })
  }

  const useStudentStats = () => {
    return useQuery({
      queryKey: ['student-stats'],
      queryFn: () => sisApi.getStudentStats(),
      staleTime: 10 * 60 * 1000, // 10 minutes
    })
  }

  // Student Mutations
  const useCreateStudent = () => {
    return useMutation({
      mutationFn: sisApi.createStudent,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['students'] })
        queryClient.invalidateQueries({ queryKey: ['student-stats'] })
        toast.success('Student registered successfully!')
      },
      onError: (error: any) => {
        console.error('Error creating student:', error)
        toast.error(error.response?.data?.detail || 'Failed to create student')
      },
    })
  }

  const useUpdateStudent = () => {
    return useMutation({
      mutationFn: ({ id, data }: { id: string; data: StudentUpdate }) =>
        sisApi.updateStudent(id, data),
      onSuccess: (_, { id }) => {
        queryClient.invalidateQueries({ queryKey: ['student', id] })
        queryClient.invalidateQueries({ queryKey: ['students'] })
        toast.success('Student updated successfully!')
      },
      onError: (error: any) => {
        console.error('Error updating student:', error)
        toast.error(error.response?.data?.detail || 'Failed to update student')
      },
    })
  }

  const useDeleteStudent = () => {
    return useMutation({
      mutationFn: ({ id, softDelete }: { id: string; softDelete?: boolean }) =>
        sisApi.deleteStudent(id, softDelete),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['students'] })
        queryClient.invalidateQueries({ queryKey: ['student-stats'] })
        toast.success('Student removed successfully!')
      },
      onError: (error: any) => {
        console.error('Error deleting student:', error)
        toast.error(error.response?.data?.detail || 'Failed to delete student')
      },
    })
  }

  // Bulk Operations
  const useBulkImportStudents = () => {
    return useMutation({
      mutationFn: sisApi.bulkImportStudents,
      onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: ['students'] })
        toast.success(`Bulk import started. Import ID: ${data.import_id}`)
      },
      onError: (error: any) => {
        console.error('Error importing students:', error)
        toast.error(error.response?.data?.detail || 'Failed to import students')
      },
    })
  }

  const useBulkImportStatus = (importId: string) => {
    return useQuery({
      queryKey: ['bulk-import-status', importId],
      queryFn: () => sisApi.getBulkImportStatus(importId),
      enabled: !!importId,
      refetchInterval: (data) => {
        // Stop polling when import is complete
        return data?.status === 'processing' ? 2000 : false
      },
    })
  }

  return {
    // Queries
    useStudents,
    useStudent,
    useStudentStats,
    useBulkImportStatus,
    
    // Mutations
    useCreateStudent,
    useUpdateStudent, 
    useDeleteStudent,
    useBulkImportStudents,
  }
}

// =====================================================
// VALIDATION UTILITIES
// =====================================================

export const validateZimbabweData = {
  nationalId: (nationalId: string): { isValid: boolean; message?: string; formatted?: string } => {
    if (!nationalId) return { isValid: true } // Optional field
    
    // Remove spaces and hyphens
    const clean = nationalId.replace(/[\s-]/g, '').toUpperCase()
    
    // Check format: 2 digits + 6 digits + 1 letter + 2 digits
    const format = /^[0-9]{2}[0-9]{6}[A-Z][0-9]{2}$/
    
    if (!format.test(clean)) {
      return {
        isValid: false,
        message: 'Invalid National ID format. Expected: 00-000000-X-00'
      }
    }
    
    // Validate province code
    const provinceCode = parseInt(clean.substring(0, 2))
    const validProvinceCodes = [
      ...Array.from({length: 10}, (_, i) => i + 1),
      ...Array.from({length: 10}, (_, i) => i + 41),
      ...Array.from({length: 10}, (_, i) => i + 61)
    ]
    
    if (!validProvinceCodes.includes(provinceCode)) {
      return {
        isValid: false,
        message: `Invalid province code: ${provinceCode}`
      }
    }
    
    // Format with hyphens
    const formatted = `${clean.substring(0, 2)}-${clean.substring(2, 8)}-${clean.substring(8, 9)}-${clean.substring(9)}`
    
    return {
      isValid: true,
      formatted
    }
  },

  phoneNumber: (phone: string): { isValid: boolean; message?: string; formatted?: string } => {
    if (!phone) return { isValid: true } // Optional field
    
    // Remove all spaces, hyphens, parentheses
    const clean = phone.replace(/[\s\-\(\)]/g, '')
    
    // Check for international format
    if (clean.startsWith('+263')) {
      const number = clean.substring(4)
      if (number.length === 9 && number[0] === '7') { // Mobile
        return { isValid: true, formatted: `+263${number}` }
      }
    } else if (clean.startsWith('0')) {
      if (clean.length === 10 && clean[1] === '7') { // Mobile
        return { isValid: true, formatted: `+263${clean.substring(1)}` }
      }
    }
    
    return {
      isValid: false,
      message: 'Invalid Zimbabwe phone number. Use format: 0712345678 or +263712345678'
    }
  },

  calculateAge: (dateOfBirth: string): number => {
    const today = new Date()
    const birthDate = new Date(dateOfBirth)
    let age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--
    }
    
    return age
  }
}

export default sisApi