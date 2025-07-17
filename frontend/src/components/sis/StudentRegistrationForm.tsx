// =====================================================
// SIS Frontend - Student Registration Form Component
// File: frontend/src/components/sis/StudentRegistrationForm.tsx
// =====================================================

import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';

// UI Components
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Icons
import { 
    User, Phone, MapPin, Heart, FileText, Users, Save, Upload, 
    AlertCircle, CheckCircle, Plus, Trash2, Eye, EyeOff 
} from 'lucide-react';

// Hooks and utilities
import { useToast } from '@/hooks/use-toast';
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { createStudent, getAvailableClasses } from '@/lib/api/sis';
import { validateZimbabwePhone, validateZimbabweProvince } from '@/lib/validations/zimbabwe';

// =====================================================
// VALIDATION SCHEMA
// =====================================================

const zimbabweProvinces = [
    'Harare', 'Bulawayo', 'Manicaland', 'Mashonaland Central',
    'Mashonaland East', 'Mashonaland West', 'Masvingo',
    'Matabeleland North', 'Matabeleland South', 'Midlands'
];

const zimbabweLanguages = [
    'English', 'Shona', 'Ndebele', 'Tonga', 'Kalanga', 'Nambya', 'Other'
];

const bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const addressSchema = z.object({
    street: z.string().min(5, "Street address must be at least 5 characters"),
    suburb: z.string().min(2, "Suburb is required"),
    city: z.string().min(2, "City is required"),
    province: z.enum(zimbabweProvinces as [string, ...string[]], {
        errorMap: () => ({ message: "Please select a valid Zimbabwe province" })
    }),
    postal_code: z.string().optional()
});

const emergencyContactSchema = z.object({
    name: z.string().min(2, "Name must be at least 2 characters").max(100),
    relationship: z.string().min(2, "Relationship is required"),
    phone: z.string().refine(validateZimbabwePhone, {
        message: "Invalid Zimbabwe phone number format (+263XXXXXXXXX or 0XXXXXXXXX)"
    }),
    alternative_phone: z.string().optional(),
    is_primary: z.boolean().default(false),
    can_pickup: z.boolean().default(true),
    address: z.string().optional()
});

const medicalConditionSchema = z.object({
    condition: z.string().min(2, "Condition name is required"),
    severity: z.enum(["Mild", "Moderate", "Severe"]),
    medication: z.string().optional(),
    notes: z.string().optional(),
    diagnosed_date: z.string().optional()
});

const allergySchema = z.object({
    allergen: z.string().min(2, "Allergen is required"),
    reaction: z.string().min(5, "Reaction description is required"),
    severity: z.enum(["Mild", "Moderate", "Severe", "Life-threatening"]),
    epipen_required: z.boolean().default(false),
    treatment: z.string().optional()
});

const studentRegistrationSchema = z.object({
    // Personal Information
    first_name: z.string().min(2, "First name is required").max(100),
    middle_name: z.string().max(100).optional(),
    last_name: z.string().min(2, "Last name is required").max(100),
    preferred_name: z.string().max(100).optional(),
    date_of_birth: z.string().refine((date) => {
        const dob = new Date(date);
        const age = new Date().getFullYear() - dob.getFullYear();
        return age >= 3 && age <= 25;
    }, "Student must be between 3 and 25 years old"),
    gender: z.enum(["Male", "Female", "Other"]),
    nationality: z.string().default("Zimbabwean"),
    home_language: z.enum(zimbabweLanguages as [string, ...string[]]).optional(),
    religion: z.string().optional(),
    tribe: z.string().optional(),

    // Contact Information
    mobile_number: z.string().optional().refine((phone) => {
        return !phone || validateZimbabwePhone(phone);
    }, "Invalid phone number format"),
    email: z.string().email("Invalid email address").optional().or(z.literal("")),

    // Address Information
    residential_address: addressSchema,
    postal_address: addressSchema.optional(),
    same_as_residential: z.boolean().default(false),

    // Academic Information
    current_grade_level: z.number().int().min(1).max(13),
    current_class_id: z.string().optional(),
    enrollment_date: z.string().default(() => format(new Date(), 'yyyy-MM-dd')),
    previous_school_name: z.string().optional(),
    transfer_reason: z.string().optional(),

    // Medical Information
    blood_type: z.enum(bloodTypes as [string, ...string[]]).optional(),
    medical_conditions: z.array(medicalConditionSchema).default([]),
    allergies: z.array(allergySchema).default([]),
    medical_aid_provider: z.string().optional(),
    medical_aid_number: z.string().optional(),
    special_needs: z.string().optional(),
    dietary_requirements: z.string().optional(),

    // Emergency Contacts (minimum 2 required)
    emergency_contacts: z.array(emergencyContactSchema)
        .min(2, "At least 2 emergency contacts are required")
        .max(5, "Maximum 5 emergency contacts allowed")
        .refine((contacts) => {
            const primaryContacts = contacts.filter(contact => contact.is_primary);
            return primaryContacts.length === 1;
        }, "Exactly one contact must be marked as primary"),

    // Additional Information
    transport_needs: z.string().optional(),
    identifying_marks: z.string().optional()
});

type StudentRegistrationForm = z.infer<typeof studentRegistrationSchema>;

// =====================================================
// COMPONENT INTERFACES
// =====================================================

interface StudentRegistrationFormProps {
    onSuccess?: (student: any) => void;
    onCancel?: () => void;
    initialData?: Partial<StudentRegistrationForm>;
    isEditing?: boolean;
}

interface FormStep {
    number: number;
    title: string;
    description: string;
    icon: React.ReactNode;
    fields: (keyof StudentRegistrationForm)[];
}

// =====================================================
// MAIN COMPONENT
// =====================================================

export function StudentRegistrationForm({
    onSuccess,
    onCancel,
    initialData,
    isEditing = false
}: StudentRegistrationFormProps) {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [currentStep, setCurrentStep] = useState(1);
    const [profilePhoto, setProfilePhoto] = useState<File | null>(null);
    const [profilePhotoPreview, setProfilePhotoPreview] = useState<string>('');
    const [showSensitiveData, setShowSensitiveData] = useState(false);

    // Offline sync integration
    const { queueOperation, syncStatus } = useOfflineSync();

    // Form setup
    const form = useForm<StudentRegistrationForm>({
        resolver: zodResolver(studentRegistrationSchema),
        defaultValues: {
            nationality: "Zimbabwean",
            gender: "Male",
            current_grade_level: 1,
            medical_conditions: [],
            allergies: [],
            emergency_contacts: [
                { name: '', relationship: '', phone: '', is_primary: true, can_pickup: true },
                { name: '', relationship: '', phone: '', is_primary: false, can_pickup: true }
            ],
            residential_address: {
                street: '',
                suburb: '',
                city: '',
                province: 'Harare'
            },
            same_as_residential: false,
            enrollment_date: format(new Date(), 'yyyy-MM-dd'),
            ...initialData
        },
        mode: 'onChange'
    });

    // Field arrays for dynamic sections
    const { fields: emergencyContactFields, append: addEmergencyContact, remove: removeEmergencyContact } = 
        useFieldArray({
            control: form.control,
            name: "emergency_contacts"
        });

    const { fields: medicalConditionFields, append: addMedicalCondition, remove: removeMedicalCondition } = 
        useFieldArray({
            control: form.control,
            name: "medical_conditions"
        });

    const { fields: allergyFields, append: addAllergy, remove: removeAllergy } = 
        useFieldArray({
            control: form.control,
            name: "allergies"
        });

    // API calls
    const { data: availableClasses, isLoading: classesLoading } = useQuery({
        queryKey: ['available-classes', form.watch('current_grade_level')],
        queryFn: () => getAvailableClasses(form.watch('current_grade_level')),
        enabled: !!form.watch('current_grade_level')
    });

    const createStudentMutation = useMutation({
        mutationFn: createStudent,
        onSuccess: (data) => {
            toast({
                title: "Success!",
                description: `Student ${data.student_number} has been registered successfully.`,
                duration: 5000
            });
            queryClient.invalidateQueries({ queryKey: ['students'] });
            onSuccess?.(data);
        },
        onError: (error: any) => {
            toast({
                title: "Registration Failed",
                description: error.response?.data?.detail || "An unexpected error occurred.",
                variant: "destructive"
            });
        }
    });

    // Form steps configuration
    const formSteps: FormStep[] = [
        {
            number: 1,
            title: "Personal Information",
            description: "Basic student details",
            icon: <User className="w-5 h-5" />,
            fields: ['first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender']
        },
        {
            number: 2,
            title: "Contact & Address",
            description: "Contact information and addresses",
            icon: <MapPin className="w-5 h-5" />,
            fields: ['mobile_number', 'email', 'residential_address', 'postal_address']
        },
        {
            number: 3,
            title: "Academic Information",
            description: "Grade level and class assignment",
            icon: <FileText className="w-5 h-5" />,
            fields: ['current_grade_level', 'current_class_id', 'previous_school_name']
        },
        {
            number: 4,
            title: "Medical Information",
            description: "Health and medical details",
            icon: <Heart className="w-5 h-5" />,
            fields: ['blood_type', 'medical_conditions', 'allergies', 'medical_aid_provider']
        },
        {
            number: 5,
            title: "Emergency Contacts",
            description: "Parent/guardian contact information",
            icon: <Users className="w-5 h-5" />,
            fields: ['emergency_contacts']
        },
        {
            number: 6,
            title: "Review & Submit",
            description: "Verify all information",
            icon: <CheckCircle className="w-5 h-5" />,
            fields: []
        }
    ];

    // Watch for same_as_residential changes
    const sameAsResidential = form.watch('same_as_residential');
    useEffect(() => {
        if (sameAsResidential) {
            const residential = form.getValues('residential_address');
            form.setValue('postal_address', residential);
        } else {
            form.setValue('postal_address', {
                street: '',
                suburb: '',
                city: '',
                province: 'Harare'
            });
        }
    }, [sameAsResidential, form]);

    // Photo upload handler
    const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                toast({
                    title: "File too large",
                    description: "Profile photo must be less than 5MB",
                    variant: "destructive"
                });
                return;
            }
            
            setProfilePhoto(file);
            const reader = new FileReader();
            reader.onload = (e) => setProfilePhotoPreview(e.target?.result as string);
            reader.readAsDataURL(file);
        }
    };

    // Step validation
    const validateCurrentStep = async (): Promise<boolean> => {
        const currentStepConfig = formSteps[currentStep - 1];
        if (currentStepConfig.fields.length === 0) return true; // Review step
        
        const result = await form.trigger(currentStepConfig.fields as any);
        return result;
    };

    // Navigation handlers
    const nextStep = async () => {
        const isValid = await validateCurrentStep();
        if (isValid && currentStep < formSteps.length) {
            setCurrentStep(currentStep + 1);
        }
    };

    const prevStep = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    // Form submission
    const handleSubmit = async (data: StudentRegistrationForm) => {
        try {
            if (navigator.onLine) {
                await createStudentMutation.mutateAsync(data);
            } else {
                // Queue for offline sync
                await queueOperation('CREATE', '/api/v1/sis/students', data);
                toast({
                    title: "Saved Offline",
                    description: "Student registration will be submitted when connection is restored.",
                    duration: 5000
                });
                onSuccess?.(data);
            }
        } catch (error) {
            console.error('Form submission error:', error);
        }
    };

    // Progress calculation
    const progress = (currentStep / formSteps.length) * 100;

    // =====================================================
    // STEP CONTENT RENDERERS
    // =====================================================

    const renderPersonalInformation = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5" />
                    Personal Information
                </CardTitle>
                <CardDescription>
                    Enter the student's basic personal details
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Profile Photo Upload */}
                <div className="flex flex-col items-center space-y-4">
                    <div className="relative">
                        {profilePhotoPreview ? (
                            <img
                                src={profilePhotoPreview}
                                alt="Profile preview"
                                className="w-32 h-32 rounded-full object-cover border-4 border-gray-200"
                            />
                        ) : (
                            <div className="w-32 h-32 rounded-full bg-gray-100 border-4 border-gray-200 flex items-center justify-center">
                                <Upload className="w-8 h-8 text-gray-400" />
                            </div>
                        )}
                    </div>
                    <div>
                        <Label htmlFor="profile-photo" className="cursor-pointer">
                            <Button variant="outline" type="button" asChild>
                                <span>
                                    <Upload className="w-4 h-4 mr-2" />
                                    Upload Photo
                                </span>
                            </Button>
                        </Label>
                        <Input
                            id="profile-photo"
                            type="file"
                            accept="image/*"
                            onChange={handlePhotoUpload}
                            className="hidden"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <Label htmlFor="first_name">First Name *</Label>
                        <Input
                            id="first_name"
                            {...form.register("first_name")}
                            placeholder="Enter first name"
                        />
                        {form.formState.errors.first_name && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.first_name.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="middle_name">Middle Name</Label>
                        <Input
                            id="middle_name"
                            {...form.register("middle_name")}
                            placeholder="Enter middle name (optional)"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="last_name">Last Name *</Label>
                        <Input
                            id="last_name"
                            {...form.register("last_name")}
                            placeholder="Enter last name"
                        />
                        {form.formState.errors.last_name && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.last_name.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="preferred_name">Preferred Name</Label>
                        <Input
                            id="preferred_name"
                            {...form.register("preferred_name")}
                            placeholder="What should we call them?"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="date_of_birth">Date of Birth *</Label>
                        <Input
                            id="date_of_birth"
                            type="date"
                            {...form.register("date_of_birth")}
                            max={format(new Date(), 'yyyy-MM-dd')}
                        />
                        {form.formState.errors.date_of_birth && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.date_of_birth.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label>Gender *</Label>
                        <Controller
                            name="gender"
                            control={form.control}
                            render={({ field }) => (
                                <Select value={field.value} onValueChange={field.onChange}>
                                    <SelectTrigger>
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
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="nationality">Nationality</Label>
                        <Input
                            id="nationality"
                            {...form.register("nationality")}
                            placeholder="Nationality"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Home Language</Label>
                        <Controller
                            name="home_language"
                            control={form.control}
                            render={({ field }) => (
                                <Select value={field.value || ""} onValueChange={field.onChange}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select home language" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {zimbabweLanguages.map((language) => (
                                            <SelectItem key={language} value={language}>
                                                {language}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="religion">Religion</Label>
                        <Input
                            id="religion"
                            {...form.register("religion")}
                            placeholder="Religion (optional)"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="tribe">Tribe</Label>
                        <Input
                            id="tribe"
                            {...form.register("tribe")}
                            placeholder="Tribe (optional)"
                        />
                    </div>
                </div>
            </CardContent>
        </Card>
    );

    const renderContactAddress = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Phone className="w-5 h-5" />
                    Contact & Address Information
                </CardTitle>
                <CardDescription>
                    Contact details and residential address
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Contact Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <Label htmlFor="mobile_number">Mobile Number</Label>
                        <Input
                            id="mobile_number"
                            {...form.register("mobile_number")}
                            placeholder="+263 77 123 4567"
                        />
                        {form.formState.errors.mobile_number && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.mobile_number.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="email">Email Address</Label>
                        <Input
                            id="email"
                            type="email"
                            {...form.register("email")}
                            placeholder="student@example.com"
                        />
                        {form.formState.errors.email && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.email.message}
                            </p>
                        )}
                    </div>
                </div>

                <Separator />

                {/* Residential Address */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Residential Address</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="residential_street">Street Address *</Label>
                            <Input
                                id="residential_street"
                                {...form.register("residential_address.street")}
                                placeholder="123 Main Street"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="residential_suburb">Suburb *</Label>
                            <Input
                                id="residential_suburb"
                                {...form.register("residential_address.suburb")}
                                placeholder="Avondale"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="residential_city">City *</Label>
                            <Input
                                id="residential_city"
                                {...form.register("residential_address.city")}
                                placeholder="Harare"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Province *</Label>
                            <Controller
                                name="residential_address.province"
                                control={form.control}
                                render={({ field }) => (
                                    <Select value={field.value} onValueChange={field.onChange}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select province" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {zimbabweProvinces.map((province) => (
                                                <SelectItem key={province} value={province}>
                                                    {province}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                )}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="residential_postal_code">Postal Code</Label>
                            <Input
                                id="residential_postal_code"
                                {...form.register("residential_address.postal_code")}
                                placeholder="Optional"
                            />
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Postal Address */}
                <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id="same-as-residential"
                            checked={form.watch("same_as_residential")}
                            onCheckedChange={(checked) => form.setValue("same_as_residential", !!checked)}
                        />
                        <Label htmlFor="same-as-residential">
                            Postal address is the same as residential address
                        </Label>
                    </div>

                    {!sameAsResidential && (
                        <>
                            <h3 className="text-lg font-semibold">Postal Address</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="postal_street">Street Address</Label>
                                    <Input
                                        id="postal_street"
                                        {...form.register("postal_address.street")}
                                        placeholder="P.O. Box 123"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="postal_suburb">Suburb</Label>
                                    <Input
                                        id="postal_suburb"
                                        {...form.register("postal_address.suburb")}
                                        placeholder="Suburb"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="postal_city">City</Label>
                                    <Input
                                        id="postal_city"
                                        {...form.register("postal_address.city")}
                                        placeholder="City"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label>Province</Label>
                                    <Controller
                                        name="postal_address.province"
                                        control={form.control}
                                        render={({ field }) => (
                                            <Select value={field.value || ""} onValueChange={field.onChange}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select province" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {zimbabweProvinces.map((province) => (
                                                        <SelectItem key={province} value={province}>
                                                            {province}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        )}
                                    />
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </CardContent>
        </Card>
    );

    const renderAcademicInformation = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Academic Information
                </CardTitle>
                <CardDescription>
                    Grade level, class assignment, and previous school details
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <Label>Current Grade Level *</Label>
                        <Controller
                            name="current_grade_level"
                            control={form.control}
                            render={({ field }) => (
                                <Select 
                                    value={field.value?.toString()} 
                                    onValueChange={(value) => field.onChange(parseInt(value))}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select grade level" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Array.from({ length: 13 }, (_, i) => i + 1).map((grade) => (
                                            <SelectItem key={grade} value={grade.toString()}>
                                                {grade <= 7 ? `Grade ${grade}` : `Form ${grade - 6}`}
                                                {grade === 12 && " (Lower 6)"}
                                                {grade === 13 && " (Upper 6)"}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                        {form.formState.errors.current_grade_level && (
                            <p className="text-sm text-red-600 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                {form.formState.errors.current_grade_level.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label>Class Assignment</Label>
                        <Controller
                            name="current_class_id"
                            control={form.control}
                            render={({ field }) => (
                                <Select 
                                    value={field.value || ""} 
                                    onValueChange={field.onChange}
                                    disabled={classesLoading || !availableClasses?.length}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={
                                            classesLoading ? "Loading classes..." : 
                                            !availableClasses?.length ? "No classes available" :
                                            "Select a class (optional)"
                                        } />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {availableClasses?.map((classItem: any) => (
                                            <SelectItem key={classItem.id} value={classItem.id}>
                                                {classItem.name} 
                                                <span className="text-gray-500 ml-2">
                                                    ({classItem.current_enrollment}/{classItem.max_capacity})
                                                </span>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="enrollment_date">Enrollment Date</Label>
                        <Input
                            id="enrollment_date"
                            type="date"
                            {...form.register("enrollment_date")}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="previous_school_name">Previous School</Label>
                        <Input
                            id="previous_school_name"
                            {...form.register("previous_school_name")}
                            placeholder="Name of previous school (if transfer)"
                        />
                    </div>

                    {form.watch("previous_school_name") && (
                        <div className="space-y-2 md:col-span-2">
                            <Label htmlFor="transfer_reason">Reason for Transfer</Label>
                            <Textarea
                                id="transfer_reason"
                                {...form.register("transfer_reason")}
                                placeholder="Briefly explain the reason for transferring schools"
                                rows={3}
                            />
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );

    const renderMedicalInformation = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Heart className="w-5 h-5" />
                    Medical Information
                    <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowSensitiveData(!showSensitiveData)}
                        className="ml-auto"
                    >
                        {showSensitiveData ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        {showSensitiveData ? "Hide" : "Show"} Details
                    </Button>
                </CardTitle>
                <CardDescription>
                    Health and medical details (confidential information)
                </CardDescription>
                <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                        Medical information is encrypted and only accessible to authorized staff and parents.
                    </AlertDescription>
                </Alert>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Basic Medical Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <Label>Blood Type</Label>
                        <Controller
                            name="blood_type"
                            control={form.control}
                            render={({ field }) => (
                                <Select value={field.value || ""} onValueChange={field.onChange}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select blood type (optional)" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {bloodTypes.map((type) => (
                                            <SelectItem key={type} value={type}>{type}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="medical_aid_provider">Medical Aid Provider</Label>
                        <Input
                            id="medical_aid_provider"
                            {...form.register("medical_aid_provider")}
                            placeholder="e.g. Premier Service Medical Aid"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="medical_aid_number">Medical Aid Number</Label>
                        <Input
                            id="medical_aid_number"
                            {...form.register("medical_aid_number")}
                            placeholder="Medical aid membership number"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="dietary_requirements">Dietary Requirements</Label>
                        <Input
                            id="dietary_requirements"
                            {...form.register("dietary_requirements")}
                            placeholder="e.g. Vegetarian, Halal, No nuts"
                        />
                    </div>
                </div>

                {showSensitiveData && (
                    <>
                        <Separator />
                        
                        {/* Medical Conditions */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">Medical Conditions</h3>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => addMedicalCondition({
                                        condition: '',
                                        severity: 'Mild',
                                        medication: '',
                                        notes: ''
                                    })}
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Condition
                                </Button>
                            </div>

                            {medicalConditionFields.map((field, index) => (
                                <Card key={field.id} className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Condition *</Label>
                                            <Input
                                                {...form.register(`medical_conditions.${index}.condition`)}
                                                placeholder="e.g. Asthma, Diabetes"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Severity</Label>
                                            <Controller
                                                name={`medical_conditions.${index}.severity`}
                                                control={form.control}
                                                render={({ field }) => (
                                                    <Select value={field.value} onValueChange={field.onChange}>
                                                        <SelectTrigger>
                                                            <SelectValue />
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

                                        <div className="space-y-2">
                                            <Label>Current Medication</Label>
                                            <Input
                                                {...form.register(`medical_conditions.${index}.medication`)}
                                                placeholder="e.g. Inhaler, Insulin"
                                            />
                                        </div>

                                        <div className="space-y-2 flex items-end">
                                            <Button
                                                type="button"
                                                variant="destructive"
                                                size="sm"
                                                onClick={() => removeMedicalCondition(index)}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>

                                        <div className="space-y-2 md:col-span-2">
                                            <Label>Additional Notes</Label>
                                            <Textarea
                                                {...form.register(`medical_conditions.${index}.notes`)}
                                                placeholder="Any additional information about this condition"
                                                rows={2}
                                            />
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        <Separator />

                        {/* Allergies */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">Allergies</h3>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => addAllergy({
                                        allergen: '',
                                        reaction: '',
                                        severity: 'Mild',
                                        epipen_required: false,
                                        treatment: ''
                                    })}
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Allergy
                                </Button>
                            </div>

                            {allergyFields.map((field, index) => (
                                <Card key={field.id} className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Allergen *</Label>
                                            <Input
                                                {...form.register(`allergies.${index}.allergen`)}
                                                placeholder="e.g. Peanuts, Shellfish"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Severity</Label>
                                            <Controller
                                                name={`allergies.${index}.severity`}
                                                control={form.control}
                                                render={({ field }) => (
                                                    <Select value={field.value} onValueChange={field.onChange}>
                                                        <SelectTrigger>
                                                            <SelectValue />
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

                                        <div className="space-y-2 md:col-span-2">
                                            <Label>Reaction *</Label>
                                            <Textarea
                                                {...form.register(`allergies.${index}.reaction`)}
                                                placeholder="Describe the allergic reaction"
                                                rows={2}
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Treatment</Label>
                                            <Input
                                                {...form.register(`allergies.${index}.treatment`)}
                                                placeholder="e.g. Antihistamine, EpiPen"
                                            />
                                        </div>

                                        <div className="space-y-2 flex items-center gap-4">
                                            <div className="flex items-center space-x-2">
                                                <Checkbox
                                                    id={`epipen-${index}`}
                                                    {...form.register(`allergies.${index}.epipen_required`)}
                                                />
                                                <Label htmlFor={`epipen-${index}`}>EpiPen Required</Label>
                                            </div>
                                            <Button
                                                type="button"
                                                variant="destructive"
                                                size="sm"
                                                onClick={() => removeAllergy(index)}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="special_needs">Special Needs or Accommodations</Label>
                            <Textarea
                                id="special_needs"
                                {...form.register("special_needs")}
                                placeholder="Any learning disabilities, physical limitations, or special accommodations needed"
                                rows={3}
                            />
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );

    const renderEmergencyContacts = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Emergency Contacts
                </CardTitle>
                <CardDescription>
                    Parent/guardian contact information (minimum 2 required)
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {emergencyContactFields.map((field, index) => (
                    <Card key={field.id} className="p-4 border-2">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">
                                Contact {index + 1}
                                {form.watch(`emergency_contacts.${index}.is_primary`) && (
                                    <Badge variant="default" className="ml-2">Primary</Badge>
                                )}
                            </h3>
                            {emergencyContactFields.length > 2 && (
                                <Button
                                    type="button"
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => removeEmergencyContact(index)}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Full Name *</Label>
                                <Input
                                    {...form.register(`emergency_contacts.${index}.name`)}
                                    placeholder="Enter full name"
                                />
                                {form.formState.errors.emergency_contacts?.[index]?.name && (
                                    <p className="text-sm text-red-600">
                                        {form.formState.errors.emergency_contacts[index]?.name?.message}
                                    </p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label>Relationship *</Label>
                                <Input
                                    {...form.register(`emergency_contacts.${index}.relationship`)}
                                    placeholder="e.g. Mother, Father, Guardian"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label>Phone Number *</Label>
                                <Input
                                    {...form.register(`emergency_contacts.${index}.phone`)}
                                    placeholder="+263 77 123 4567"
                                />
                                {form.formState.errors.emergency_contacts?.[index]?.phone && (
                                    <p className="text-sm text-red-600">
                                        {form.formState.errors.emergency_contacts[index]?.phone?.message}
                                    </p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label>Alternative Phone</Label>
                                <Input
                                    {...form.register(`emergency_contacts.${index}.alternative_phone`)}
                                    placeholder="Secondary phone number"
                                />
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <Label>Address</Label>
                                <Textarea
                                    {...form.register(`emergency_contacts.${index}.address`)}
                                    placeholder="Home or work address"
                                    rows={2}
                                />
                            </div>

                            <div className="space-y-4 md:col-span-2">
                                <div className="flex flex-wrap gap-4">
                                    <div className="flex items-center space-x-2">
                                        <Controller
                                            name={`emergency_contacts.${index}.is_primary`}
                                            control={form.control}
                                            render={({ field }) => (
                                                <Checkbox
                                                    id={`primary-${index}`}
                                                    checked={field.value}
                                                    onCheckedChange={(checked) => {
                                                        // Ensure only one primary contact
                                                        if (checked) {
                                                            emergencyContactFields.forEach((_, i) => {
                                                                if (i !== index) {
                                                                    form.setValue(`emergency_contacts.${i}.is_primary`, false);
                                                                }
                                                            });
                                                        }
                                                        field.onChange(checked);
                                                    }}
                                                />
                                            )}
                                        />
                                        <Label htmlFor={`primary-${index}`}>Primary Contact</Label>
                                    </div>

                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id={`pickup-${index}`}
                                            {...form.register(`emergency_contacts.${index}.can_pickup`)}
                                        />
                                        <Label htmlFor={`pickup-${index}`}>Authorized for Pickup</Label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>
                ))}

                {emergencyContactFields.length < 5 && (
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => addEmergencyContact({
                            name: '',
                            relationship: '',
                            phone: '',
                            is_primary: false,
                            can_pickup: true
                        })}
                        className="w-full"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Emergency Contact
                    </Button>
                )}

                {form.formState.errors.emergency_contacts && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                            {form.formState.errors.emergency_contacts.message}
                        </AlertDescription>
                    </Alert>
                )}
            </CardContent>
        </Card>
    );

    const renderReviewAndSubmit = () => {
        const formData = form.getValues();
        
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Review & Submit
                    </CardTitle>
                    <CardDescription>
                        Please review all information before submitting
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Summary Cards */}
                    <div className="grid gap-4">
                        {/* Personal Info Summary */}
                        <Card className="p-4">
                            <h3 className="font-semibold mb-2">Personal Information</h3>
                            <div className="text-sm space-y-1">
                                <p><strong>Name:</strong> {`${formData.first_name} ${formData.middle_name || ''} ${formData.last_name}`.trim()}</p>
                                <p><strong>Date of Birth:</strong> {formData.date_of_birth}</p>
                                <p><strong>Gender:</strong> {formData.gender}</p>
                                <p><strong>Nationality:</strong> {formData.nationality}</p>
                                {formData.home_language && <p><strong>Home Language:</strong> {formData.home_language}</p>}
                            </div>
                        </Card>

                        {/* Contact Summary */}
                        <Card className="p-4">
                            <h3 className="font-semibold mb-2">Contact Information</h3>
                            <div className="text-sm space-y-1">
                                {formData.mobile_number && <p><strong>Mobile:</strong> {formData.mobile_number}</p>}
                                {formData.email && <p><strong>Email:</strong> {formData.email}</p>}
                                <p><strong>Address:</strong> {formData.residential_address.street}, {formData.residential_address.suburb}, {formData.residential_address.city}, {formData.residential_address.province}</p>
                            </div>
                        </Card>

                        {/* Academic Summary */}
                        <Card className="p-4">
                            <h3 className="font-semibold mb-2">Academic Information</h3>
                            <div className="text-sm space-y-1">
                                <p><strong>Grade Level:</strong> {formData.current_grade_level <= 7 ? `Grade ${formData.current_grade_level}` : `Form ${formData.current_grade_level - 6}`}</p>
                                <p><strong>Enrollment Date:</strong> {formData.enrollment_date}</p>
                                {formData.previous_school_name && <p><strong>Previous School:</strong> {formData.previous_school_name}</p>}
                            </div>
                        </Card>

                        {/* Emergency Contacts Summary */}
                        <Card className="p-4">
                            <h3 className="font-semibold mb-2">Emergency Contacts</h3>
                            <div className="text-sm space-y-2">
                                {formData.emergency_contacts.map((contact, index) => (
                                    <div key={index} className="border-l-2 border-gray-200 pl-3">
                                        <p><strong>{contact.name}</strong> ({contact.relationship})</p>
                                        <p>{contact.phone}</p>
                                        {contact.is_primary && <Badge variant="default" className="text-xs">Primary Contact</Badge>}
                                    </div>
                                ))}
                            </div>
                        </Card>

                        {/* Medical Summary */}
                        {(formData.medical_conditions.length > 0 || formData.allergies.length > 0) && (
                            <Card className="p-4">
                                <h3 className="font-semibold mb-2">Medical Information</h3>
                                <div className="text-sm space-y-1">
                                    {formData.blood_type && <p><strong>Blood Type:</strong> {formData.blood_type}</p>}
                                    {formData.medical_conditions.length > 0 && (
                                        <p><strong>Medical Conditions:</strong> {formData.medical_conditions.map(c => c.condition).join(", ")}</p>
                                    )}
                                    {formData.allergies.length > 0 && (
                                        <p><strong>Allergies:</strong> {formData.allergies.map(a => a.allergen).join(", ")}</p>
                                    )}
                                </div>
                            </Card>
                        )}
                    </div>

                    {/* Offline Status */}
                    {syncStatus === 'offline' && (
                        <Alert>
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                                You are currently offline. The student registration will be saved locally and submitted when connection is restored.
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Form Errors */}
                    {Object.keys(form.formState.errors).length > 0 && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                                Please correct the errors in previous steps before submitting.
                            </AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>
        );
    };

    // =====================================================
    // RENDER MAIN COMPONENT
    // =====================================================

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold">
                    {isEditing ? "Edit Student Information" : "Student Registration"}
                </h1>
                <p className="text-gray-600">
                    {isEditing ? "Update student details" : "Register a new student in the system"}
                </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                    <span>Step {currentStep} of {formSteps.length}</span>
                    <span>{Math.round(progress)}% Complete</span>
                </div>
                <Progress value={progress} className="h-2" />
            </div>

            {/* Step Navigator */}
            <div className="flex items-center justify-between overflow-x-auto pb-2">
                {formSteps.map((step, index) => (
                    <React.Fragment key={step.number}>
                        <div className="flex flex-col items-center min-w-0 flex-1">
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                                    currentStep === step.number
                                        ? 'bg-blue-600 text-white'
                                        : currentStep > step.number
                                        ? 'bg-green-600 text-white'
                                        : 'bg-gray-200 text-gray-600'
                                }`}
                            >
                                {currentStep > step.number ? (
                                    <CheckCircle className="w-5 h-5" />
                                ) : (
                                    step.icon
                                )}
                            </div>
                            <div className="mt-2 text-center">
                                <div className="text-sm font-medium">{step.title}</div>
                                <div className="text-xs text-gray-500 hidden sm:block">{step.description}</div>
                            </div>
                        </div>
                        {index < formSteps.length - 1 && (
                            <div
                                className={`flex-1 h-0.5 mx-2 ${
                                    currentStep > step.number ? 'bg-green-600' : 'bg-gray-200'
                                }`}
                            />
                        )}
                    </React.Fragment>
                ))}
            </div>

            {/* Form Content */}
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                {currentStep === 1 && renderPersonalInformation()}
                {currentStep === 2 && renderContactAddress()}
                {currentStep === 3 && renderAcademicInformation()}
                {currentStep === 4 && renderMedicalInformation()}
                {currentStep === 5 && renderEmergencyContacts()}
                {currentStep === 6 && renderReviewAndSubmit()}

                {/* Navigation Buttons */}
                <div className="flex justify-between">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={currentStep === 1 ? onCancel : prevStep}
                        disabled={createStudentMutation.isPending}
                    >
                        {currentStep === 1 ? 'Cancel' : 'Previous'}
                    </Button>

                    <div className="flex space-x-2">
                        {currentStep < formSteps.length ? (
                            <Button 
                                type="button" 
                                onClick={nextStep}
                                disabled={createStudentMutation.isPending}
                            >
                                Next
                            </Button>
                        ) : (
                            <Button 
                                type="submit" 
                                disabled={createStudentMutation.isPending || Object.keys(form.formState.errors).length > 0}
                                className="flex items-center"
                            >
                                {createStudentMutation.isPending ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                        {isEditing ? 'Updating...' : 'Registering...'}
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4 mr-2" />
                                        {isEditing ? 'Update Student' : 'Register Student'}
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                </div>
            </form>
        </div>
    );
}