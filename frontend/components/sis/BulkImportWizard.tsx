"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Upload, 
  Download, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Users,
  FileSpreadsheet,
  Clock,
  Loader2
} from "lucide-react"
import { useSISHooks, type BulkImportStatus } from "@/lib/sis-api"
// Note: react-dropzone would normally be imported here
// For now, using native file input as fallback
import { toast } from "sonner"

interface BulkImportWizardProps {
  onComplete?: () => void
  onCancel?: () => void
}

export default function BulkImportWizard({ onComplete, onCancel }: BulkImportWizardProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [importId, setImportId] = useState<string | null>(null)
  
  const { useBulkImportStudents, useBulkImportStatus } = useSISHooks()
  const bulkImportMutation = useBulkImportStudents()
  const { data: importStatus, isLoading: statusLoading } = useBulkImportStatus(importId || "")

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error("File size should not exceed 10MB")
        return
      }
      
      if (!['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        toast.error("Please upload a CSV or Excel file")
        return
      }
      
      setUploadedFile(file)
      setCurrentStep(2)
    }
  }, [])

  const handleImport = async () => {
    if (!uploadedFile) return

    try {
      const result = await bulkImportMutation.mutateAsync(uploadedFile)
      setImportId(result.import_id)
      setCurrentStep(3)
      toast.success("Import started successfully!")
    } catch (error) {
      console.error("Import failed:", error)
      toast.error("Failed to start import. Please try again.")
    }
  }

  const downloadTemplate = () => {
    // Create a sample CSV template
    const csvContent = `first_name,middle_name,last_name,date_of_birth,gender,nationality,home_language,mobile_number,email,street,suburb,city,province,postal_code,current_grade_level,enrollment_date,previous_school_name,guardian_name,guardian_phone,guardian_relationship
Tinashe,Joseph,Mukamuri,2005-03-15,Male,Zimbabwean,Shona,0771234567,tj.mukamuri@school.zw,123 Main Street,Avondale,Harare,Harare,HRE,11,2025-01-15,St Johns Primary,Mary Mukamuri,0772345678,Mother
Chipo,Grace,Nyathi,2006-07-20,Female,Zimbabwean,Ndebele,0773456789,chipo.nyathi@school.zw,456 Second Ave,Belvedere,Harare,Harare,HRE,10,2025-01-15,Central Primary,John Nyathi,0774567890,Father`

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'student_import_template.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <FileSpreadsheet className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-bold mb-2">Bulk Import Students</h2>
        <p className="text-muted-foreground">
          Upload a CSV or Excel file to import multiple students at once
        </p>
      </div>

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Before you start:</strong>
          <ul className="mt-2 list-disc list-inside space-y-1">
            <li>Download and use our template to ensure proper formatting</li>
            <li>All required fields must be completed for each student</li>
            <li>Phone numbers should be in Zimbabwe format (077xxxxxxx or +263xxxxxxx)</li>
            <li>Date format should be YYYY-MM-DD (e.g., 2005-03-15)</li>
            <li>Maximum file size: 10MB</li>
          </ul>
        </AlertDescription>
      </Alert>

      <div className="flex justify-center">
        <Button onClick={downloadTemplate} variant="outline" className="mb-6">
          <Download className="mr-2 h-4 w-4" />
          Download CSV Template
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="border-2 border-dashed rounded-lg p-8 text-center border-muted-foreground/25 hover:border-primary/50 transition-colors">
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <div>
              <p className="text-lg font-medium mb-2">
                Choose a file to upload
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                Supports CSV, XLS, and XLSX files up to 10MB
              </p>
              <div className="relative">
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept=".csv,.xls,.xlsx"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Button type="button" variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Browse Files
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
        <h2 className="text-2xl font-bold mb-2">File Ready for Import</h2>
        <p className="text-muted-foreground">
          Review the file details below and start the import process
        </p>
      </div>

      {uploadedFile && (
        <Card>
          <CardHeader>
            <CardTitle>File Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">File Name</p>
                <p className="font-medium">{uploadedFile.name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">File Size</p>
                <p className="font-medium">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">File Type</p>
                <p className="font-medium">{uploadedFile.type}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Last Modified</p>
                <p className="font-medium">{new Date(uploadedFile.lastModified).toLocaleDateString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Important:</strong> The import process will validate all data according to Zimbabwe education standards.
          Any errors will be reported and those records will be skipped. You can download a detailed error report after the import completes.
        </AlertDescription>
      </Alert>

      <div className="flex justify-center space-x-4">
        <Button variant="outline" onClick={() => setCurrentStep(1)}>
          Choose Different File
        </Button>
        <Button 
          onClick={handleImport} 
          disabled={bulkImportMutation.isPending}
          className="min-w-32"
        >
          {bulkImportMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Starting Import...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Start Import
            </>
          )}
        </Button>
      </div>
    </div>
  )

  const renderStep3 = () => {
    if (!importStatus || statusLoading) {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 text-primary animate-spin mb-4" />
            <h2 className="text-2xl font-bold mb-2">Processing Import</h2>
            <p className="text-muted-foreground">
              Please wait while we process your file...
            </p>
          </div>
          
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span>Processing...</span>
                  <span>Please wait</span>
                </div>
                <Progress value={undefined} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    const isComplete = importStatus.status === 'completed' || importStatus.status === 'failed'
    const progressPercentage = importStatus.total_records > 0 
      ? ((importStatus.successful + importStatus.failed) / importStatus.total_records) * 100 
      : 0

    return (
      <div className="space-y-6">
        <div className="text-center">
          {importStatus.status === 'completed' ? (
            <>
              <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
              <h2 className="text-2xl font-bold mb-2">Import Completed!</h2>
              <p className="text-muted-foreground">
                Your student data has been successfully imported
              </p>
            </>
          ) : importStatus.status === 'failed' ? (
            <>
              <XCircle className="mx-auto h-12 w-12 text-red-600 mb-4" />
              <h2 className="text-2xl font-bold mb-2">Import Failed</h2>
              <p className="text-muted-foreground">
                There was an error processing your file
              </p>
            </>
          ) : (
            <>
              <Clock className="mx-auto h-12 w-12 text-primary mb-4" />
              <h2 className="text-2xl font-bold mb-2">Import in Progress</h2>
              <p className="text-muted-foreground">
                Processing your student data...
              </p>
            </>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Import Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold">{importStatus.total_records}</div>
                  <div className="text-sm text-muted-foreground">Total Records</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{importStatus.successful}</div>
                  <div className="text-sm text-muted-foreground">Successful</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{importStatus.failed}</div>
                  <div className="text-sm text-muted-foreground">Failed</div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Progress</span>
                  <span>{progressPercentage.toFixed(1)}%</span>
                </div>
                <Progress value={progressPercentage} className="h-2" />
              </div>

              <div className="flex items-center justify-center">
                <Badge 
                  variant={importStatus.status === 'completed' ? 'default' : 
                           importStatus.status === 'failed' ? 'destructive' : 'secondary'}
                >
                  {importStatus.status.charAt(0).toUpperCase() + importStatus.status.slice(1)}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {importStatus.errors && importStatus.errors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertCircle className="mr-2 h-5 w-5 text-orange-500" />
                Import Errors ({importStatus.errors.length})
              </CardTitle>
              <CardDescription>
                The following records could not be imported due to validation errors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-64 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Error</TableHead>
                      <TableHead>Student Name</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {importStatus.errors.slice(0, 10).map((error, index) => (
                      <TableRow key={index}>
                        <TableCell>{error.row}</TableCell>
                        <TableCell className="text-red-600">{error.error}</TableCell>
                        <TableCell>
                          {error.data?.first_name} {error.data?.last_name}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {importStatus.errors.length > 10 && (
                  <p className="text-sm text-muted-foreground mt-2 text-center">
                    ... and {importStatus.errors.length - 10} more errors
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {isComplete && (
          <div className="flex justify-center space-x-4">
            <Button variant="outline" onClick={() => {
              setCurrentStep(1)
              setUploadedFile(null)
              setImportId(null)
            }}>
              Import Another File
            </Button>
            <Button onClick={onComplete}>
              <Users className="mr-2 h-4 w-4" />
              View Students
            </Button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Bulk Import Students</h1>
        <p className="text-muted-foreground">
          Import multiple student records from CSV or Excel files
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center justify-center space-x-4">
        {[1, 2, 3].map((step) => (
          <div key={step} className="flex items-center">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full border-2 ${
              currentStep >= step 
                ? 'border-primary bg-primary text-primary-foreground' 
                : 'border-muted-foreground/25 bg-muted text-muted-foreground'
            }`}>
              {currentStep > step ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                step
              )}
            </div>
            {step < 3 && (
              <div className={`w-16 h-0.5 ${
                currentStep > step ? 'bg-primary' : 'bg-muted-foreground/25'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="p-8">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </CardContent>
      </Card>

      {/* Footer */}
      {onCancel && currentStep < 3 && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      )}
    </div>
  )
}