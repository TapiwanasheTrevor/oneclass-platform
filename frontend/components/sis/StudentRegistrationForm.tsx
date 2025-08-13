"use client"

import { useState } from "react"
import { useForm, Controller, useFieldArray } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { ChevronLeft, ChevronRight, Check, User, MapPin, GraduationCap, Heart, Users, Plus, Minus, AlertCircle } from "lucide-react"
import { useSISHooks, validateZimbabweData, ZIMBABWE_PROVINCES, HOME_LANGUAGES, BLOOD_TYPES, RELATIONSHIPS, type StudentCreate, type EmergencyContact, type MedicalCondition, type Allergy } from "@/lib/sis-api"
import { toast } from "sonner"

// =====================================================
// VALIDATION SCHEMAS
// =====================================================

const emergencyContactSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  relationship: z.string().min(1, "Relationship is required"),
  phone: z.string().min(1, "Phone number is required").refine((phone) => {
    const validation = validateZimbabweData.phoneNumber(phone)
    return validation.isValid
  }, "Invalid Zimbabwe phone number format"),
  alternative_phone: z.string().optional(),
  is_primary: z.boolean(),
  can_pickup: z.boolean(),
  address: z.string().optional(),
})

const medicalConditionSchema = z.object({
  condition: z.string().min(2, "Condition name is required"),
  severity: z.enum(['Mild', 'Moderate', 'Severe']),
  medication: z.string().optional(),
  notes: z.string().optional(),
  diagnosed_date: z.string().optional(),
  doctor_name: z.string().optional(),
})

const allergySchema = z.object({
  allergen: z.string().min(2, "Allergen is required"),
  reaction: z.string().min(5, "Reaction description is required"),
  severity: z.enum(['Mild', 'Moderate', 'Severe', 'Life-threatening']),
  epipen_required: z.boolean(),
  treatment: z.string().optional(),
})

const studentRegistrationSchema = z.object({
  // Personal Information
  first_name: z.string().min(2, "First name must be at least 2 characters"),
  middle_name: z.string().optional(),
  last_name: z.string().min(2, "Last name must be at least 2 characters"),
  preferred_name: z.string().optional(),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  gender: z.enum(['Male', 'Female', 'Other']),
  nationality: z.string().default('Zimbabwean'),
  home_language: z.enum(['English', 'Shona', 'Ndebele', 'Tonga', 'Kalanga', 'Nambya', 'Other']).optional(),
  religion: z.string().optional(),
  tribe: z.string().optional(),
  
  // Contact Information
  mobile_number: z.string().optional().refine((phone) => {
    if (!phone) return true
    const validation = validateZimbabweData.phoneNumber(phone)
    return validation.isValid
  }, "Invalid Zimbabwe phone number format"),
  email: z.string().email().optional().or(z.literal('')),
  
  // Address
  residential_address: z.object({
    street: z.string().min(5, "Street address is required"),
    suburb: z.string().min(2, "Suburb is required"),
    city: z.string().min(2, "City is required"),
    province: z.enum(['Harare', 'Bulawayo', 'Manicaland', 'Mashonaland Central', 'Mashonaland East', 'Mashonaland West', 'Masvingo', 'Matabeleland North', 'Matabeleland South', 'Midlands']),
    postal_code: z.string().optional(),
  }),
  
  // Academic Information
  current_grade_level: z.number().min(1).max(13),
  enrollment_date: z.string().min(1, "Enrollment date is required"),
  previous_school_name: z.string().optional(),
  transfer_reason: z.string().optional(),
  
  // Medical Information
  blood_type: z.enum(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']).optional(),
  medical_conditions: z.array(medicalConditionSchema).default([]),
  allergies: z.array(allergySchema).default([]),
  medical_aid_provider: z.string().optional(),
  medical_aid_number: z.string().optional(),
  dietary_requirements: z.string().optional(),
  
  // Emergency Contacts
  emergency_contacts: z.array(emergencyContactSchema).min(2, "At least 2 emergency contacts are required"),
  
  // Additional Information
  transport_needs: z.string().optional(),
  identifying_marks: z.string().optional(),
})

type StudentRegistrationForm = z.infer<typeof studentRegistrationSchema>

// Form steps
const FORM_STEPS = [
  { id: 'personal', title: 'Personal Information', icon: User },
  { id: 'contact', title: 'Contact Details', icon: MapPin },
  { id: 'academic', title: 'Academic Information', icon: GraduationCap },
  { id: 'medical', title: 'Medical Information', icon: Heart },
  { id: 'guardian', title: 'Emergency Contacts', icon: Users },
  { id: 'review', title: 'Review & Submit', icon: Check }
]

interface StudentRegistrationFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export default function StudentRegistrationForm({ onSuccess, onCancel }: StudentRegistrationFormProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const { useCreateStudent } = useSISHooks()
  const createStudentMutation = useCreateStudent()

  const form = useForm<StudentRegistrationForm>({
    resolver: zodResolver(studentRegistrationSchema),
    defaultValues: {
      nationality: 'Zimbabwean',
      enrollment_date: new Date().toISOString().split('T')[0],
      residential_address: {
        street: '',
        suburb: '',
        city: '',
        province: 'Harare',
        postal_code: '',
      },
      medical_conditions: [],
      allergies: [],
      emergency_contacts: [
        {
          name: '',
          relationship: '',
          phone: '',
          is_primary: true,
          can_pickup: true,
        },
        {
          name: '',
          relationship: '',
          phone: '',
          is_primary: false,
          can_pickup: true,
        }
      ],
    },
  })

  const { control, handleSubmit, formState: { errors }, watch, setValue, trigger, getValues } = form
  
  // Field arrays for dynamic fields
  const { fields: medicalConditionFields, append: appendMedicalCondition, remove: removeMedicalCondition } = useFieldArray({
    control,
    name: 'medical_conditions',
  })
  
  const { fields: allergyFields, append: appendAllergy, remove: removeAllergy } = useFieldArray({
    control,
    name: 'allergies',
  })
  
  const { fields: emergencyContactFields, append: appendEmergencyContact, remove: removeEmergencyContact } = useFieldArray({
    control,
    name: 'emergency_contacts',
  })

  const handleNext = async () => {
    // Validate current step
    let fieldsToValidate: (keyof StudentRegistrationForm)[] = []
    
    switch (currentStep) {
      case 0: // Personal Information
        fieldsToValidate = ['first_name', 'last_name', 'date_of_birth', 'gender']
        break
      case 1: // Contact Details
        fieldsToValidate = ['residential_address']
        break
      case 2: // Academic Information
        fieldsToValidate = ['current_grade_level', 'enrollment_date']
        break
      case 3: // Medical Information
        // Optional fields, no validation needed
        break
      case 4: // Emergency Contacts
        fieldsToValidate = ['emergency_contacts']
        break
    }
    
    const isValid = await trigger(fieldsToValidate as any)
    
    if (isValid && currentStep < FORM_STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const onSubmit = async (data: StudentRegistrationForm) => {
    try {
      // Transform data to match API schema
      const studentData: StudentCreate = {
        ...data,
        current_grade_level: Number(data.current_grade_level),
        // Ensure phone numbers are properly formatted
        mobile_number: data.mobile_number ? validateZimbabweData.phoneNumber(data.mobile_number).formatted : undefined,
        emergency_contacts: data.emergency_contacts.map(contact => ({
          ...contact,
          phone: validateZimbabweData.phoneNumber(contact.phone).formatted || contact.phone,
        })),
      }

      await createStudentMutation.mutateAsync(studentData)
      
      if (onSuccess) {
        onSuccess()
      } else {
        // Default redirect to students list
        setTimeout(() => {
          window.location.href = '/students'
        }, 2000)
      }
      
    } catch (error) {
      console.error('Error submitting form:', error)
      // Error handled by mutation onError callback
    }
  }

  // Render functions for each step
  const renderPersonalInfo = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="first_name">First Name *</Label>
          <Controller
            name="first_name"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="first_name"
                placeholder="Enter first name"
                className={errors.first_name ? "border-red-500" : ""}
              />
            )}
          />
          {errors.first_name && (
            <p className="text-sm text-red-500">{errors.first_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="middle_name">Middle Name</Label>
          <Controller
            name="middle_name"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="middle_name"
                placeholder="Enter middle name"
              />
            )}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="last_name">Last Name *</Label>
        <Controller
          name="last_name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              id="last_name"
              placeholder="Enter last name"
              className={errors.last_name ? "border-red-500" : ""}
            />
          )}
        />
        {errors.last_name && (
          <p className="text-sm text-red-500">{errors.last_name.message}</p>
        )}
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="preferred_name">Preferred Name</Label>
        <Controller
          name="preferred_name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              id="preferred_name"
              placeholder="Enter preferred name (optional)"
            />
          )}
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="date_of_birth">Date of Birth *</Label>
          <Controller
            name="date_of_birth"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="date_of_birth"
                type="date"
                className={errors.date_of_birth ? "border-red-500" : ""}
              />
            )}
          />
          {errors.date_of_birth && (
            <p className="text-sm text-red-500">{errors.date_of_birth.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="gender">Gender *</Label>
          <Controller
            name="gender"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger className={errors.gender ? "border-red-500" : ""}>
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Male">Male</SelectItem>
                  <SelectItem value="Female">Female</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          {errors.gender && (
            <p className="text-sm text-red-500">{errors.gender.message}</p>
          )}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="nationality">Nationality</Label>
          <Controller
            name="nationality"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="nationality"
                placeholder="Enter nationality"
              />
            )}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="home_language">Home Language</Label>
          <Controller
            name="home_language"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger>
                  <SelectValue placeholder="Select home language" />
                </SelectTrigger>
                <SelectContent>
                  {HOME_LANGUAGES.map(language => (
                    <SelectItem key={language} value={language}>{language}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="religion">Religion</Label>
          <Controller
            name="religion"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="religion"
                placeholder="Enter religion (optional)"
              />
            )}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tribe">Tribe</Label>
          <Controller
            name="tribe"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="tribe"
                placeholder="Enter tribe (optional)"
              />
            )}
          />
        </div>
      </div>
    </div>
  )

  const renderContactDetails = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="mobile_number">Mobile Number</Label>
          <Controller
            name="mobile_number"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="mobile_number"
                placeholder="+263 xxx xxx xxx"
                className={errors.mobile_number ? "border-red-500" : ""}
              />
            )}
          />
          {errors.mobile_number && (
            <p className="text-sm text-red-500">{errors.mobile_number.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email Address</Label>
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="email"
                type="email"
                placeholder="Enter email address"
                className={errors.email ? "border-red-500" : ""}
              />
            )}
          />
          {errors.email && (
            <p className="text-sm text-red-500">{errors.email.message}</p>
          )}
        </div>
      </div>
      
      <Separator />
      
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">Residential Address</h3>
        
        <div className="space-y-2">
          <Label htmlFor="street">Street Address *</Label>
          <Controller
            name="residential_address.street"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="street"
                placeholder="Enter street address"
                className={errors.residential_address?.street ? "border-red-500" : ""}
              />
            )}
          />
          {errors.residential_address?.street && (
            <p className="text-sm text-red-500">{errors.residential_address.street.message}</p>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="suburb">Suburb/Township</Label>
            <Controller
              name="residential_address.suburb"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="suburb"
                  placeholder="Enter suburb or township"
                  className={errors.residential_address?.suburb ? "border-red-500" : ""}
                />
              )}
            />
            {errors.residential_address?.suburb && (
              <p className="text-sm text-red-500">{errors.residential_address.suburb.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="city">City *</Label>
            <Controller
              name="residential_address.city"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="city"
                  placeholder="Enter city"
                  className={errors.residential_address?.city ? "border-red-500" : ""}
                />
              )}
            />
            {errors.residential_address?.city && (
              <p className="text-sm text-red-500">{errors.residential_address.city.message}</p>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="province">Province *</Label>
            <Controller
              name="residential_address.province"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger className={errors.residential_address?.province ? "border-red-500" : ""}>
                    <SelectValue placeholder="Select province" />
                  </SelectTrigger>
                  <SelectContent>
                    {ZIMBABWE_PROVINCES.map(province => (
                      <SelectItem key={province} value={province}>{province}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.residential_address?.province && (
              <p className="text-sm text-red-500">{errors.residential_address.province.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="postal_code">Postal Code</Label>
            <Controller
              name="residential_address.postal_code"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="postal_code"
                  placeholder="Enter postal code"
                />
              )}
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderAcademicInfo = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="current_grade_level">Current Grade Level *</Label>
        <Controller
          name="current_grade_level"
          control={control}
          render={({ field }) => (
            <Select onValueChange={(value) => field.onChange(Number(value))} value={field.value?.toString()}>
              <SelectTrigger className={errors.current_grade_level ? "border-red-500" : ""}>
                <SelectValue placeholder="Select grade level" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 13 }, (_, i) => i + 1).map(grade => (
                  <SelectItem key={grade} value={grade.toString()}>
                    {grade <= 7 ? `Grade ${grade}` : `Form ${grade - 6}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.current_grade_level && (
          <p className="text-sm text-red-500">{errors.current_grade_level.message}</p>
        )}
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="enrollment_date">Enrollment Date *</Label>
        <Controller
          name="enrollment_date"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              id="enrollment_date"
              type="date"
              className={errors.enrollment_date ? "border-red-500" : ""}
            />
          )}
        />
        {errors.enrollment_date && (
          <p className="text-sm text-red-500">{errors.enrollment_date.message}</p>
        )}
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="previous_school_name">Previous School</Label>
        <Controller
          name="previous_school_name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              id="previous_school_name"
              placeholder="Name of previous school (if any)"
            />
          )}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="transfer_reason">Transfer Reason</Label>
        <Controller
          name="transfer_reason"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              id="transfer_reason"
              placeholder="Reason for transfer (if applicable)"
              rows={3}
            />
          )}
        />
      </div>
    </div>
  )

  const renderMedicalInfo = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Basic Medical Information</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="blood_type">Blood Type</Label>
          <Controller
            name="blood_type"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger>
                  <SelectValue placeholder="Select blood type" />
                </SelectTrigger>
                <SelectContent>
                  {BLOOD_TYPES.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="medical_aid_provider">Medical Aid Provider</Label>
          <Controller
            name="medical_aid_provider"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="medical_aid_provider"
                placeholder="e.g., PSMAS, CIMAS, First Mutual"
              />
            )}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="medical_aid_number">Medical Aid Number</Label>
        <Controller
          name="medical_aid_number"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              id="medical_aid_number"
              placeholder="Enter medical aid membership number"
            />
          )}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="dietary_requirements">Dietary Requirements</Label>
        <Controller
          name="dietary_requirements"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              id="dietary_requirements"
              placeholder="Any dietary restrictions or special requirements"
              rows={3}
            />
          )}
        />
      </div>
      
      <Separator />
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Medical Conditions</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => appendMedicalCondition({ condition: '', severity: 'Mild', medication: '', notes: '' })}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Condition
          </Button>
        </div>
        
        {medicalConditionFields.map((field, index) => (
          <Card key={field.id} className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Medical Condition {index + 1}</h4>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeMedicalCondition(index)}
                >
                  <Minus className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Condition Name</Label>
                  <Controller
                    name={`medical_conditions.${index}.condition`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        placeholder="e.g., Asthma, Diabetes"
                      />
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Severity</Label>
                  <Controller
                    name={`medical_conditions.${index}.severity`}
                    control={control}
                    render={({ field }) => (
                      <Select onValueChange={field.onChange} value={field.value}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select severity" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Mild">Mild</SelectItem>
                          <SelectItem value="Moderate">Moderate</SelectItem>
                          <SelectItem value="Severe">Severe</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Medication</Label>
                <Controller
                  name={`medical_conditions.${index}.medication`}
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder="Current medication for this condition"
                    />
                  )}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Notes</Label>
                <Controller
                  name={`medical_conditions.${index}.notes`}
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      placeholder="Additional notes about this condition"
                      rows={2}
                    />
                  )}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      <Separator />
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Allergies</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => appendAllergy({ allergen: '', reaction: '', severity: 'Mild', epipen_required: false })}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Allergy
          </Button>
        </div>
        
        {allergyFields.map((field, index) => (
          <Card key={field.id} className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Allergy {index + 1}</h4>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeAllergy(index)}
                >
                  <Minus className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Allergen</Label>
                  <Controller
                    name={`allergies.${index}.allergen`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        placeholder="e.g., Peanuts, Shellfish"
                      />
                    )}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Severity</Label>
                  <Controller
                    name={`allergies.${index}.severity`}
                    control={control}
                    render={({ field }) => (
                      <Select onValueChange={field.onChange} value={field.value}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select severity" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Mild">Mild</SelectItem>
                          <SelectItem value="Moderate">Moderate</SelectItem>
                          <SelectItem value="Severe">Severe</SelectItem>
                          <SelectItem value="Life-threatening">Life-threatening</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Reaction</Label>
                <Controller
                  name={`allergies.${index}.reaction`}
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      placeholder="Describe the allergic reaction"
                      rows={2}
                    />
                  )}
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Controller
                  name={`allergies.${index}.epipen_required`}
                  control={control}
                  render={({ field }) => (
                    <Checkbox
                      id={`epipen-${index}`}
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
                <Label htmlFor={`epipen-${index}`}>EpiPen required</Label>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )

  const renderEmergencyContacts = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Emergency Contacts</h3>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => appendEmergencyContact({ name: '', relationship: '', phone: '', is_primary: false, can_pickup: true })}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Contact
        </Button>
      </div>
      
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          At least 2 emergency contacts are required. These contacts will be notified in case of emergencies.
        </AlertDescription>
      </Alert>
      
      {emergencyContactFields.map((field, index) => (
        <Card key={field.id} className="p-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Emergency Contact {index + 1}</h4>
              {emergencyContactFields.length > 2 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeEmergencyContact(index)}
                >
                  <Minus className="h-4 w-4" />
                </Button>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Full Name *</Label>
                <Controller
                  name={`emergency_contacts.${index}.name`}
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder="Enter full name"
                      className={errors.emergency_contacts?.[index]?.name ? "border-red-500" : ""}
                    />
                  )}
                />
                {errors.emergency_contacts?.[index]?.name && (
                  <p className="text-sm text-red-500">{errors.emergency_contacts[index]?.name?.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Relationship *</Label>
                <Controller
                  name={`emergency_contacts.${index}.relationship`}
                  control={control}
                  render={({ field }) => (
                    <Select onValueChange={field.onChange} value={field.value}>
                      <SelectTrigger className={errors.emergency_contacts?.[index]?.relationship ? "border-red-500" : ""}>
                        <SelectValue placeholder="Select relationship" />
                      </SelectTrigger>
                      <SelectContent>
                        {RELATIONSHIPS.map(relationship => (
                          <SelectItem key={relationship} value={relationship}>{relationship}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                {errors.emergency_contacts?.[index]?.relationship && (
                  <p className="text-sm text-red-500">{errors.emergency_contacts[index]?.relationship?.message}</p>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Phone Number *</Label>
                <Controller
                  name={`emergency_contacts.${index}.phone`}
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder="+263 xxx xxx xxx"
                      className={errors.emergency_contacts?.[index]?.phone ? "border-red-500" : ""}
                    />
                  )}
                />
                {errors.emergency_contacts?.[index]?.phone && (
                  <p className="text-sm text-red-500">{errors.emergency_contacts[index]?.phone?.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Alternative Phone</Label>
                <Controller
                  name={`emergency_contacts.${index}.alternative_phone`}
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder="+263 xxx xxx xxx"
                    />
                  )}
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Controller
                  name={`emergency_contacts.${index}.is_primary`}
                  control={control}
                  render={({ field }) => (
                    <Checkbox
                      id={`primary-${index}`}
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
                <Label htmlFor={`primary-${index}`}>Primary contact</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Controller
                  name={`emergency_contacts.${index}.can_pickup`}
                  control={control}
                  render={({ field }) => (
                    <Checkbox
                      id={`pickup-${index}`}
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
                <Label htmlFor={`pickup-${index}`}>Can pick up student</Label>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Address</Label>
              <Controller
                name={`emergency_contacts.${index}.address`}
                control={control}
                render={({ field }) => (
                  <Textarea
                    {...field}
                    placeholder="Enter contact's address (optional)"
                    rows={2}
                  />
                )}
              />
            </div>
          </div>
        </Card>
      ))}
    </div>
  )

  const renderReview = () => {
    const formData = getValues()
    
    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">Review Your Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Name:</span>
                <span className="text-sm font-medium">{formData.first_name} {formData.middle_name} {formData.last_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Preferred Name:</span>
                <span className="text-sm font-medium">{formData.preferred_name || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Date of Birth:</span>
                <span className="text-sm font-medium">{formData.date_of_birth}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Gender:</span>
                <span className="text-sm font-medium">{formData.gender}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Language:</span>
                <span className="text-sm font-medium">{formData.home_language || 'Not specified'}</span>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Contact Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Phone:</span>
                <span className="text-sm font-medium">{formData.mobile_number || 'Not provided'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Email:</span>
                <span className="text-sm font-medium">{formData.email || 'Not provided'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Address:</span>
                <span className="text-sm font-medium">{formData.residential_address.street}, {formData.residential_address.city}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Province:</span>
                <span className="text-sm font-medium">{formData.residential_address.province}</span>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Academic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Grade Level:</span>
                <span className="text-sm font-medium">
                  {formData.current_grade_level <= 7 ? `Grade ${formData.current_grade_level}` : `Form ${formData.current_grade_level - 6}`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Enrollment Date:</span>
                <span className="text-sm font-medium">{formData.enrollment_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Previous School:</span>
                <span className="text-sm font-medium">{formData.previous_school_name || 'None'}</span>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Medical Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Blood Type:</span>
                <span className="text-sm font-medium">{formData.blood_type || 'Not specified'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Medical Aid:</span>
                <span className="text-sm font-medium">{formData.medical_aid_provider || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Medical Conditions:</span>
                <span className="text-sm font-medium">{formData.medical_conditions.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Allergies:</span>
                <span className="text-sm font-medium">{formData.allergies.length}</span>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Emergency Contacts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {formData.emergency_contacts.map((contact, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-muted rounded-lg">
                  <div>
                    <div className="font-medium">{contact.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {contact.relationship} • {contact.phone}
                      {contact.is_primary && <Badge className="ml-2" variant="secondary">Primary</Badge>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderPersonalInfo()
      case 1:
        return renderContactDetails()
      case 2:
        return renderAcademicInfo()
      case 3:
        return renderMedicalInfo()
      case 4:
        return renderEmergencyContacts()
      case 5:
        return renderReview()
      default:
        return null
    }
  }

  if (createStudentMutation.isSuccess) {
    return (
      <div className="space-y-6">
        <Card className="mx-auto max-w-2xl">
          <CardContent className="p-8 text-center">
            <div className="mb-6">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <Check className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Registration Successful!</h2>
              <p className="text-muted-foreground">
                Student registration has been submitted successfully. You will receive confirmation details shortly.
              </p>
            </div>
            <div className="space-y-2">
              <Button onClick={() => window.location.href = '/students'} className="w-full">
                View Student Directory
              </Button>
              <Button variant="outline" onClick={() => window.location.href = '/'} className="w-full">
                Return to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            {FORM_STEPS.map((step, index) => {
              const Icon = step.icon
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    index === currentStep 
                      ? 'border-primary bg-primary text-primary-foreground' 
                      : index < currentStep 
                        ? 'border-primary bg-primary text-primary-foreground' 
                        : 'border-muted-foreground/25 bg-muted text-muted-foreground'
                  }`}>
                    {index < currentStep ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span className="mt-2 text-xs text-center font-medium max-w-20">
                    {step.title}
                  </span>
                </div>
              )
            })}
          </div>
          <div className="mt-4">
            <Progress value={((currentStep + 1) / FORM_STEPS.length) * 100} className="h-2" />
          </div>
        </CardHeader>
      </Card>

      {/* Form Content */}
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle>{FORM_STEPS[currentStep].title}</CardTitle>
            <CardDescription>
              {currentStep === 0 && "Enter the student's personal information"}
              {currentStep === 1 && "Provide contact details and address information"}
              {currentStep === 2 && "Enter academic and school information"}
              {currentStep === 3 && "Add medical information and health details"}
              {currentStep === 4 && "Add emergency contact information"}
              {currentStep === 5 && "Review all information before submitting"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderStepContent()}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <Button 
            type="button"
            variant="outline" 
            onClick={handleBack}
            disabled={currentStep === 0}
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          <div className="flex space-x-2">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            {currentStep < FORM_STEPS.length - 1 ? (
              <Button type="button" onClick={handleNext}>
                Next
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button 
                type="submit"
                disabled={createStudentMutation.isPending}
              >
                {createStudentMutation.isPending ? 'Submitting...' : 'Submit Registration'}
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}