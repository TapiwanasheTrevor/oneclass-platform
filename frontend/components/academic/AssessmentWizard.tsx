"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { 
  ChevronLeft,
  ChevronRight,
  Save,
  RefreshCw,
  Plus,
  Trash2,
  FileText,
  Clock,
  Users,
  Target,
  BookOpen,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Settings,
  Edit,
  Eye,
  Copy,
  Share,
  Download,
  Upload,
  GraduationCap,
  Calculator,
  Award,
  BarChart3,
  Info
} from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { format } from "date-fns"

import { 
  useAcademicHooks,
  type AssessmentCreate,
  type Question,
  type QuestionCreate,
  zimbabweTerms,
  formatTerm
} from "@/lib/academic-api"

const assessmentSchema = z.object({
  name: z.string().min(1, "Assessment name is required").max(100),
  description: z.string().optional(),
  subject_id: z.string().min(1, "Subject is required"),
  class_id: z.string().min(1, "Class is required"),
  teacher_id: z.string().min(1, "Teacher is required"),
  term_number: z.number().min(1).max(3),
  assessment_type: z.enum(["test", "quiz", "assignment", "project", "practical", "exam"]),
  assessment_category: z.enum(["continuous", "summative", "formative"]),
  total_marks: z.number().min(1, "Total marks must be at least 1"),
  pass_mark: z.number().min(0),
  weight_percentage: z.number().min(1).max(100),
  assessment_date: z.string(),
  due_date: z.string().optional(),
  duration_minutes: z.number().optional(),
  instructions: z.string().optional(),
  resources_allowed: z.array(z.string()).default([]),
  is_group_assessment: z.boolean().default(false),
  academic_year_id: z.string().min(1, "Academic year is required")
})

const questionSchema = z.object({
  question_text: z.string().min(1, "Question text is required"),
  question_type: z.enum(["multiple_choice", "short_answer", "essay", "true_false", "numerical"]),
  marks: z.number().min(0.5, "Marks must be at least 0.5"),
  difficulty_level: z.enum(["easy", "medium", "hard"]),
  topic: z.string().optional(),
  correct_answer: z.string().optional(),
  answer_options: z.array(z.string()).default([]),
  explanation: z.string().optional(),
  time_limit_minutes: z.number().optional()
})

type AssessmentFormData = z.infer<typeof assessmentSchema>
type QuestionFormData = z.infer<typeof questionSchema>

interface AssessmentWizardProps {
  academicYearId: string
  subjectId?: string
  classId?: string
  className?: string
  onComplete?: (assessment: any) => void
}

interface WizardStep {
  id: string
  title: string
  description: string
  component: React.ReactNode
  isValid: boolean
}

const ASSESSMENT_TYPES = [
  { value: "test", label: "Test", description: "Formal in-class assessment" },
  { value: "quiz", label: "Quiz", description: "Short assessment or pop quiz" },
  { value: "assignment", label: "Assignment", description: "Take-home work" },
  { value: "project", label: "Project", description: "Extended research or creative work" },
  { value: "practical", label: "Practical", description: "Hands-on lab or field work" },
  { value: "exam", label: "Exam", description: "Major formal examination" }
]

const QUESTION_TYPES = [
  { value: "multiple_choice", label: "Multiple Choice", description: "Question with predefined options" },
  { value: "short_answer", label: "Short Answer", description: "Brief written response" },
  { value: "essay", label: "Essay", description: "Extended written response" },
  { value: "true_false", label: "True/False", description: "Binary choice question" },
  { value: "numerical", label: "Numerical", description: "Mathematical calculation" }
]

const DIFFICULTY_LEVELS = [
  { value: "easy", label: "Easy", color: "text-green-600", description: "Basic recall and understanding" },
  { value: "medium", label: "Medium", color: "text-yellow-600", description: "Application and analysis" },
  { value: "hard", label: "Hard", color: "text-red-600", description: "Synthesis and evaluation" }
]

const COMMON_RESOURCES = [
  "Calculator", "Formula sheet", "Dictionary", "Computer", "Internet access",
  "Textbook", "Notes", "Graph paper", "Ruler", "Protractor"
]

export default function AssessmentWizard({ 
  academicYearId, 
  subjectId, 
  classId, 
  className,
  onComplete 
}: AssessmentWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [questions, setQuestions] = useState<QuestionFormData[]>([])
  const [isQuestionDialogOpen, setIsQuestionDialogOpen] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null)

  const { useCreateAssessment, useSubjects } = useAcademicHooks()
  
  const { data: subjects } = useSubjects()
  const createAssessmentMutation = useCreateAssessment()

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    trigger,
    getValues
  } = useForm<AssessmentFormData>({
    resolver: zodResolver(assessmentSchema),
    defaultValues: {
      academic_year_id: academicYearId,
      subject_id: subjectId || "",
      class_id: classId || "",
      teacher_id: "", // Will be set from auth context
      term_number: 1,
      assessment_type: "test",
      assessment_category: "continuous",
      total_marks: 100,
      pass_mark: 50,
      weight_percentage: 20,
      assessment_date: new Date().toISOString().split('T')[0],
      duration_minutes: 90,
      resources_allowed: [],
      is_group_assessment: false
    }
  })

  const questionForm = useForm<QuestionFormData>({
    resolver: zodResolver(questionSchema),
    defaultValues: {
      question_type: "multiple_choice",
      marks: 1,
      difficulty_level: "medium",
      answer_options: ["", "", "", ""],
      time_limit_minutes: undefined
    }
  })

  const watchedValues = watch()
  const watchedQuestionType = questionForm.watch("question_type")

  const calculateTotalMarks = () => {
    return questions.reduce((total, q) => total + q.marks, 0)
  }

  const getDifficultyDistribution = () => {
    const total = questions.length
    if (total === 0) return { easy: 0, medium: 0, hard: 0 }
    
    const counts = questions.reduce((acc, q) => {
      acc[q.difficulty_level]++
      return acc
    }, { easy: 0, medium: 0, hard: 0 })
    
    return {
      easy: (counts.easy / total) * 100,
      medium: (counts.medium / total) * 100,
      hard: (counts.hard / total) * 100
    }
  }

  const handleAddQuestion = (data: QuestionFormData) => {
    if (editingQuestion !== null) {
      const updatedQuestions = [...questions]
      updatedQuestions[editingQuestion] = data
      setQuestions(updatedQuestions)
      setEditingQuestion(null)
    } else {
      setQuestions(prev => [...prev, data])
    }
    
    setIsQuestionDialogOpen(false)
    questionForm.reset()
    toast.success(editingQuestion !== null ? "Question updated" : "Question added")
  }

  const handleEditQuestion = (index: number) => {
    const question = questions[index]
    questionForm.reset(question)
    setEditingQuestion(index)
    setIsQuestionDialogOpen(true)
  }

  const handleDeleteQuestion = (index: number) => {
    setQuestions(prev => prev.filter((_, i) => i !== index))
    toast.success("Question deleted")
  }

  const handleCreateAssessment = async (data: AssessmentFormData) => {
    try {
      const assessment = await createAssessmentMutation.mutateAsync({
        ...data,
        total_marks: calculateTotalMarks() || data.total_marks
      })
      
      toast.success("Assessment created successfully!")
      onComplete?.(assessment)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const nextStep = async () => {
    const stepValid = await trigger()
    if (stepValid && currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Assessment Name *</Label>
          <Input
            id="name"
            placeholder="e.g., Mid-Term Mathematics Test"
            {...register("name")}
          />
          {errors.name && (
            <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>
          )}
        </div>
        <div>
          <Label htmlFor="assessment_type">Assessment Type *</Label>
          <Select 
            value={watchedValues.assessment_type} 
            onValueChange={(value) => setValue("assessment_type", value as any)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ASSESSMENT_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div>
                    <div className="font-medium">{type.label}</div>
                    <div className="text-xs text-muted-foreground">{type.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Brief description of the assessment objectives and content"
          {...register("description")}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <Label htmlFor="term_number">Term *</Label>
          <Select 
            value={watchedValues.term_number?.toString()} 
            onValueChange={(value) => setValue("term_number", parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {zimbabweTerms.map((term) => (
                <SelectItem key={term.value} value={term.value.toString()}>
                  {formatTerm(term.value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="subject_id">Subject *</Label>
          <Select 
            value={watchedValues.subject_id} 
            onValueChange={(value) => setValue("subject_id", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select subject" />
            </SelectTrigger>
            <SelectContent>
              {subjects?.items?.map((subject: any) => (
                <SelectItem key={subject.id} value={subject.id}>
                  {subject.name} ({subject.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.subject_id && (
            <p className="text-sm text-red-600 mt-1">{errors.subject_id.message}</p>
          )}
        </div>
        <div>
          <Label htmlFor="class_id">Class *</Label>
          <Input
            id="class_id"
            placeholder="e.g., Form 4A"
            {...register("class_id")}
          />
          {errors.class_id && (
            <p className="text-sm text-red-600 mt-1">{errors.class_id.message}</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderScoringSettings = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <Label htmlFor="total_marks">Total Marks *</Label>
          <Input
            id="total_marks"
            type="number"
            min="1"
            {...register("total_marks", { valueAsNumber: true })}
          />
          {errors.total_marks && (
            <p className="text-sm text-red-600 mt-1">{errors.total_marks.message}</p>
          )}
          {questions.length > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              Questions total: {calculateTotalMarks()} marks
            </p>
          )}
        </div>
        <div>
          <Label htmlFor="pass_mark">Pass Mark *</Label>
          <Input
            id="pass_mark"
            type="number"
            min="0"
            max={watchedValues.total_marks}
            {...register("pass_mark", { valueAsNumber: true })}
          />
        </div>
        <div>
          <Label htmlFor="weight_percentage">Weight Percentage *</Label>
          <Input
            id="weight_percentage"
            type="number"
            min="1"
            max="100"
            {...register("weight_percentage", { valueAsNumber: true })}
          />
          <p className="text-xs text-muted-foreground mt-1">
            % contribution to final grade
          </p>
        </div>
      </div>

      <div>
        <Label>Assessment Category</Label>
        <RadioGroup 
          value={watchedValues.assessment_category}
          onValueChange={(value) => setValue("assessment_category", value as any)}
          className="mt-2"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="continuous" id="continuous" />
            <Label htmlFor="continuous">Continuous Assessment</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="formative" id="formative" />
            <Label htmlFor="formative">Formative Assessment</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="summative" id="summative" />
            <Label htmlFor="summative">Summative Assessment</Label>
          </div>
        </RadioGroup>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Assessment Categories:</strong>
          <ul className="mt-2 text-sm space-y-1">
            <li>• <strong>Continuous:</strong> Regular ongoing assessment</li>
            <li>• <strong>Formative:</strong> Assessment for learning and feedback</li>
            <li>• <strong>Summative:</strong> Assessment of learning outcomes</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  )

  const renderScheduleSettings = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="assessment_date">Assessment Date *</Label>
          <Input
            id="assessment_date"
            type="date"
            {...register("assessment_date")}
          />
        </div>
        <div>
          <Label htmlFor="due_date">Due Date (for assignments)</Label>
          <Input
            id="due_date"
            type="date"
            {...register("due_date")}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="duration_minutes">Duration (minutes)</Label>
          <Input
            id="duration_minutes"
            type="number"
            min="1"
            placeholder="90"
            {...register("duration_minutes", { valueAsNumber: true })}
          />
        </div>
        <div className="flex items-center space-x-2 pt-6">
          <Checkbox
            id="is_group_assessment"
            checked={watchedValues.is_group_assessment}
            onCheckedChange={(checked) => setValue("is_group_assessment", checked as boolean)}
          />
          <Label htmlFor="is_group_assessment">Group Assessment</Label>
        </div>
      </div>

      <div>
        <Label>Allowed Resources</Label>
        <div className="grid grid-cols-3 gap-2 mt-2">
          {COMMON_RESOURCES.map((resource) => (
            <div key={resource} className="flex items-center space-x-2">
              <Checkbox
                id={resource}
                checked={watchedValues.resources_allowed.includes(resource)}
                onCheckedChange={(checked) => {
                  const current = watchedValues.resources_allowed
                  if (checked) {
                    setValue("resources_allowed", [...current, resource])
                  } else {
                    setValue("resources_allowed", current.filter(r => r !== resource))
                  }
                }}
              />
              <Label htmlFor={resource} className="text-sm">{resource}</Label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <Label htmlFor="instructions">Instructions for Students</Label>
        <Textarea
          id="instructions"
          placeholder="Special instructions, rules, or guidelines for this assessment..."
          {...register("instructions")}
        />
      </div>
    </div>
  )

  const renderQuestionBank = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Question Bank</h3>
          <p className="text-sm text-muted-foreground">
            Create questions for this assessment
          </p>
        </div>
        <Button onClick={() => setIsQuestionDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Question
        </Button>
      </div>

      {questions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{questions.length}</div>
                <div className="text-sm text-muted-foreground">Total Questions</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{calculateTotalMarks()}</div>
                <div className="text-sm text-muted-foreground">Total Marks</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {questions.length > 0 ? (calculateTotalMarks() / questions.length).toFixed(1) : 0}
                </div>
                <div className="text-sm text-muted-foreground">Avg Marks/Question</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Difficulty Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {DIFFICULTY_LEVELS.map((level) => {
                const percentage = getDifficultyDistribution()[level.value as keyof ReturnType<typeof getDifficultyDistribution>]
                return (
                  <div key={level.value} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className={level.color}>
                        {level.label}
                      </Badge>
                      <span className="text-sm">{level.description}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Progress value={percentage} className="w-20 h-2" />
                      <span className="text-sm w-10">{percentage.toFixed(0)}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {questions.map((question, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline">
                      Question {index + 1}
                    </Badge>
                    <Badge variant="outline" className="capitalize">
                      {question.question_type.replace('_', ' ')}
                    </Badge>
                    <Badge 
                      variant="outline" 
                      className={DIFFICULTY_LEVELS.find(d => d.value === question.difficulty_level)?.color}
                    >
                      {question.difficulty_level}
                    </Badge>
                    <Badge variant="secondary">
                      {question.marks} marks
                    </Badge>
                  </div>
                  <p className="text-sm mb-2">{question.question_text}</p>
                  
                  {question.question_type === "multiple_choice" && question.answer_options.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {question.answer_options.filter(opt => opt.trim()).map((option, optIndex) => (
                        <div key={optIndex} className="text-xs text-muted-foreground">
                          {String.fromCharCode(65 + optIndex)}) {option}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditQuestion(index)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteQuestion(index)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {questions.length === 0 && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-semibold mb-2">No questions yet</h3>
              <p className="mb-4">Start building your assessment by adding questions</p>
              <Button onClick={() => setIsQuestionDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Your First Question
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )

  const renderReview = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckCircle2 className="mr-2 h-5 w-5 text-green-600" />
            Assessment Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium">Assessment Name</Label>
              <p className="text-sm">{watchedValues.name}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Type</Label>
              <p className="text-sm capitalize">{watchedValues.assessment_type}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Total Marks</Label>
              <p className="text-sm">{calculateTotalMarks() || watchedValues.total_marks}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Pass Mark</Label>
              <p className="text-sm">{watchedValues.pass_mark}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Weight</Label>
              <p className="text-sm">{watchedValues.weight_percentage}%</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Assessment Date</Label>
              <p className="text-sm">{format(new Date(watchedValues.assessment_date), 'PPP')}</p>
            </div>
          </div>

          {watchedValues.description && (
            <div>
              <Label className="text-sm font-medium">Description</Label>
              <p className="text-sm text-muted-foreground">{watchedValues.description}</p>
            </div>
          )}

          {watchedValues.resources_allowed.length > 0 && (
            <div>
              <Label className="text-sm font-medium">Allowed Resources</Label>
              <div className="flex flex-wrap gap-1 mt-1">
                {watchedValues.resources_allowed.map((resource) => (
                  <Badge key={resource} variant="outline" className="text-xs">
                    {resource}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Questions Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Total Questions:</span>
                <span className="font-medium">{questions.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Total Marks:</span>
                <span className="font-medium">{calculateTotalMarks()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Question Types:</span>
                <div className="text-right">
                  {Array.from(new Set(questions.map(q => q.question_type))).map((type, index, arr) => (
                    <span key={type} className="capitalize">
                      {type.replace('_', ' ')}{index < arr.length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertDescription>
          Review all details carefully before creating the assessment. Once created, some settings cannot be changed.
        </AlertDescription>
      </Alert>
    </div>
  )

  const steps: WizardStep[] = [
    {
      id: "basic",
      title: "Basic Information",
      description: "Assessment name, type, and subject",
      component: renderBasicInfo(),
      isValid: !errors.name && !errors.subject_id && !errors.class_id
    },
    {
      id: "scoring",
      title: "Scoring & Grading",
      description: "Marks, pass criteria, and weighting",
      component: renderScoringSettings(),
      isValid: !errors.total_marks && !errors.pass_mark && !errors.weight_percentage
    },
    {
      id: "schedule",
      title: "Schedule & Settings",
      description: "Dates, duration, and resources",
      component: renderScheduleSettings(),
      isValid: !errors.assessment_date
    },
    {
      id: "questions",
      title: "Question Bank",
      description: "Create assessment questions",
      component: renderQuestionBank(),
      isValid: true // Optional step
    },
    {
      id: "review",
      title: "Review & Create",
      description: "Final review before creation",
      component: renderReview(),
      isValid: true
    }
  ]

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assessment Creation Wizard</h1>
          <p className="text-muted-foreground">
            Create a new assessment with guided setup
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            Step {currentStep + 1} of {steps.length}
          </Badge>
        </div>
      </div>

      {/* Progress Bar */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <Progress value={((currentStep + 1) / steps.length) * 100} className="h-2" />
            <div className="flex justify-between text-sm">
              {steps.map((step, index) => (
                <div 
                  key={step.id} 
                  className={`text-center ${index === currentStep ? 'font-medium' : 'text-muted-foreground'}`}
                >
                  <div className={`w-8 h-8 rounded-full mx-auto mb-1 flex items-center justify-center text-xs ${
                    index < currentStep ? 'bg-green-600 text-white' :
                    index === currentStep ? 'bg-primary text-primary-foreground' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {index < currentStep ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
                  </div>
                  <div className="font-medium">{step.title}</div>
                  <div className="text-xs text-muted-foreground">{step.description}</div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{steps[currentStep].title}</CardTitle>
          <CardDescription>{steps[currentStep].description}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(handleCreateAssessment)}>
            {steps[currentStep].component}
          </form>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Previous
        </Button>
        
        <div className="flex items-center space-x-2">
          {currentStep === steps.length - 1 ? (
            <Button 
              onClick={handleSubmit(handleCreateAssessment)}
              disabled={createAssessmentMutation.isPending}
              size="lg"
            >
              {createAssessmentMutation.isPending ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Create Assessment
                </>
              )}
            </Button>
          ) : (
            <Button onClick={nextStep}>
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Question Dialog */}
      <Dialog open={isQuestionDialogOpen} onOpenChange={setIsQuestionDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingQuestion !== null ? 'Edit Question' : 'Add Question'}
            </DialogTitle>
            <DialogDescription>
              Create a new question for this assessment
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={questionForm.handleSubmit(handleAddQuestion)} className="space-y-4">
            <div>
              <Label htmlFor="question_text">Question Text *</Label>
              <Textarea
                id="question_text"
                placeholder="Enter your question here..."
                {...questionForm.register("question_text")}
              />
              {questionForm.formState.errors.question_text && (
                <p className="text-sm text-red-600 mt-1">
                  {questionForm.formState.errors.question_text.message}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="question_type">Question Type *</Label>
                <Select 
                  value={watchedQuestionType} 
                  onValueChange={(value) => questionForm.setValue("question_type", value as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {QUESTION_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-xs text-muted-foreground">{type.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="marks">Marks *</Label>
                <Input
                  id="marks"
                  type="number"
                  step="0.5"
                  min="0.5"
                  {...questionForm.register("marks", { valueAsNumber: true })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="difficulty_level">Difficulty Level *</Label>
                <Select 
                  value={questionForm.watch("difficulty_level")} 
                  onValueChange={(value) => questionForm.setValue("difficulty_level", value as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DIFFICULTY_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className={level.color}>
                            {level.label}
                          </Badge>
                          <span className="text-xs">{level.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="topic">Topic/Chapter</Label>
                <Input
                  id="topic"
                  placeholder="e.g., Algebra, Fractions"
                  {...questionForm.register("topic")}
                />
              </div>
            </div>

            {watchedQuestionType === "multiple_choice" && (
              <div>
                <Label>Answer Options</Label>
                <div className="space-y-2 mt-2">
                  {questionForm.watch("answer_options").map((_, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <Label className="w-6">{String.fromCharCode(65 + index)})</Label>
                      <Input
                        placeholder={`Option ${String.fromCharCode(65 + index)}`}
                        value={questionForm.watch("answer_options")[index]}
                        onChange={(e) => {
                          const options = [...questionForm.watch("answer_options")]
                          options[index] = e.target.value
                          questionForm.setValue("answer_options", options)
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(watchedQuestionType === "short_answer" || watchedQuestionType === "numerical") && (
              <div>
                <Label htmlFor="correct_answer">Correct Answer/Sample Answer</Label>
                <Input
                  id="correct_answer"
                  placeholder="Enter the correct answer or sample answer"
                  {...questionForm.register("correct_answer")}
                />
              </div>
            )}

            <div>
              <Label htmlFor="explanation">Explanation/Teaching Notes</Label>
              <Textarea
                id="explanation"
                placeholder="Optional explanation for the answer or teaching notes..."
                {...questionForm.register("explanation")}
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsQuestionDialogOpen(false)
                  setEditingQuestion(null)
                  questionForm.reset()
                }}
              >
                Cancel
              </Button>
              <Button type="submit">
                <Save className="mr-2 h-4 w-4" />
                {editingQuestion !== null ? 'Update Question' : 'Add Question'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}