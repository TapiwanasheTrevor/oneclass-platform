/**
 * Bulk Onboarding Manager
 * Handles mass user imports and onboarding for schools
 */

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Upload, Users, FileText, Download, CheckCircle, 
  AlertTriangle, Info, RefreshCw, Eye, Mail,
  School, GraduationCap, Heart, UserPlus
} from 'lucide-react';
import { toast } from 'sonner';
import { useDropzone } from 'react-dropzone';

import { useAuth, usePermissions, PlatformRole, SchoolRole } from '@/hooks/useAuth';

interface BulkUser {
  row: number;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  platformRole: PlatformRole;
  schoolRole: SchoolRole;
  department?: string;
  employeeId?: string;
  studentId?: string;
  currentGrade?: string;
  parentEmail?: string;
  subjects?: string[];
  status: 'pending' | 'processing' | 'success' | 'error';
  error?: string;
  userId?: string;
}

interface BulkImportJob {
  id: string;
  filename: string;
  totalUsers: number;
  processedUsers: number;
  successfulUsers: number;
  failedUsers: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  completedAt?: string;
  errors: Array<{
    row: number;
    email: string;
    error: string;
  }>;
}

export const BulkOnboardingManager: React.FC = () => {
  const { token } = useAuth();
  const { canManageUsers, isPlatformAdmin, isSchoolAdmin } = usePermissions();
  
  const [activeTab, setActiveTab] = useState('upload');
  const [users, setUsers] = useState<BulkUser[]>([]);
  const [importJobs, setImportJobs] = useState<BulkImportJob[]>([]);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedJob, setSelectedJob] = useState<BulkImportJob | null>(null);

  // File upload handling
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
      toast.error('Please upload a CSV or Excel file');
      return;
    }

    try {
      setProcessing(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/bulk-import/preview', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const { users: parsedUsers, errors } = await response.json();
        
        if (errors.length > 0) {
          toast.error(`Found ${errors.length} errors in the file. Please fix them before proceeding.`);
        }
        
        setUsers(parsedUsers.map((user: any, index: number) => ({
          ...user,
          row: index + 2, // Account for header row
          status: 'pending' as const
        })));
        
        setActiveTab('preview');
        toast.success(`Parsed ${parsedUsers.length} users from file`);
      } else {
        throw new Error('Failed to parse file');
      }
    } catch (error) {
      toast.error('Failed to parse file. Please check the format and try again.');
      console.error('Error parsing file:', error);
    } finally {
      setProcessing(false);
    }
  }, [token]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  // Start bulk import process
  const startBulkImport = async () => {
    try {
      setProcessing(true);
      const response = await fetch('/api/v1/bulk-import/process', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ users }),
      });

      if (response.ok) {
        const job = await response.json();
        setImportJobs(prev => [job, ...prev]);
        setSelectedJob(job);
        setActiveTab('progress');
        
        // Start polling for progress
        pollJobProgress(job.id);
        
        toast.success('Bulk import started');
      } else {
        throw new Error('Failed to start bulk import');
      }
    } catch (error) {
      toast.error('Failed to start bulk import');
      console.error('Error starting bulk import:', error);
    } finally {
      setProcessing(false);
    }
  };

  // Poll job progress
  const pollJobProgress = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/bulk-import/jobs/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const job = await response.json();
          setSelectedJob(job);
          setImportJobs(prev => prev.map(j => j.id === jobId ? job : j));
          
          const progress = job.totalUsers > 0 ? (job.processedUsers / job.totalUsers) * 100 : 0;
          setUploadProgress(progress);

          if (job.status === 'processing') {
            setTimeout(poll, 2000); // Poll every 2 seconds
          } else {
            setProcessing(false);
            if (job.status === 'completed') {
              toast.success(`Bulk import completed! ${job.successfulUsers} users processed successfully.`);
            } else {
              toast.error(`Bulk import failed. Check the errors tab for details.`);
            }
          }
        }
      } catch (error) {
        console.error('Error polling job progress:', error);
        setTimeout(poll, 5000); // Retry after 5 seconds
      }
    };
    
    poll();
  };

  // Fetch import history
  const fetchImportHistory = async () => {
    try {
      const response = await fetch('/api/v1/bulk-import/jobs', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const jobs = await response.json();
        setImportJobs(jobs);
      }
    } catch (error) {
      console.error('Error fetching import history:', error);
    }
  };

  React.useEffect(() => {
    if (canManageUsers) {
      fetchImportHistory();
    }
  }, [canManageUsers]);

  // Download template
  const downloadTemplate = () => {
    const csvContent = [
      'email,firstName,lastName,phone,platformRole,schoolRole,department,employeeId,studentId,currentGrade,parentEmail,subjects',
      'john.teacher@example.com,John,Doe,+263771234567,teacher,teacher,Mathematics,EMP001,,,,"Mathematics,Physics"',
      'mary.parent@example.com,Mary,Smith,+263778765432,parent,parent,,,,,,',
      'student@example.com,Jane,Student,+263771111111,student,student,,,STU001,Form 4A,mary.parent@example.com,',
      'admin@example.com,Admin,User,+263779999999,school_admin,principal,Administration,EMP002,,,,'
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'oneclass_bulk_import_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!canManageUsers) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">Access Denied</h3>
          <p className="text-gray-500">You need user management permissions to access bulk onboarding.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6" />
            Bulk User Onboarding
          </h1>
          <p className="text-gray-600">Import multiple users at once with automated onboarding</p>
        </div>
        
        <Button variant="outline" onClick={downloadTemplate} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Download Template
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="upload">Upload File</TabsTrigger>
          <TabsTrigger value="preview" disabled={users.length === 0}>
            Preview ({users.length})
          </TabsTrigger>
          <TabsTrigger value="progress" disabled={!selectedJob}>
            Progress
          </TabsTrigger>
          <TabsTrigger value="history">Import History</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload User File
              </CardTitle>
              <CardDescription>
                Upload a CSV or Excel file containing user information. Download the template for the correct format.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                {isDragActive ? (
                  <p className="text-blue-600">Drop the file here...</p>
                ) : (
                  <div>
                    <p className="text-lg font-medium text-gray-600 mb-2">
                      Drag and drop your file here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports CSV and Excel files (.csv, .xlsx, .xls)
                    </p>
                  </div>
                )}
              </div>
              
              {processing && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Processing file...</span>
                  </div>
                  <Progress value={50} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* File Format Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                File Format Requirements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Required Columns:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• <strong>email</strong>: User's email address (must be unique)</li>
                    <li>• <strong>firstName</strong>: User's first name</li>
                    <li>• <strong>lastName</strong>: User's last name</li>
                    <li>• <strong>platformRole</strong>: teacher, parent, student, staff, school_admin</li>
                    <li>• <strong>schoolRole</strong>: principal, teacher, student, parent, etc.</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Optional Columns:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• <strong>phone</strong>: Phone number with country code</li>
                    <li>• <strong>department</strong>: Department or subject area</li>
                    <li>• <strong>employeeId</strong>: Staff/teacher ID number</li>
                    <li>• <strong>studentId</strong>: Student ID number</li>
                    <li>• <strong>currentGrade</strong>: Student's current grade/form</li>
                    <li>• <strong>parentEmail</strong>: Parent's email (for students)</li>
                    <li>• <strong>subjects</strong>: Teaching subjects (comma-separated)</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold">Preview Users</h3>
              <p className="text-gray-600">Review the users before starting the import process</p>
            </div>
            
            <Button 
              onClick={startBulkImport} 
              disabled={processing || users.length === 0}
              className="flex items-center gap-2"
            >
              {processing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              {processing ? 'Starting Import...' : `Import ${users.length} Users`}
            </Button>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="max-h-96 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Platform Role</TableHead>
                      <TableHead>School Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.row}>
                        <TableCell>{user.row}</TableCell>
                        <TableCell className="font-medium">
                          {user.firstName} {user.lastName}
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {user.platformRole.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="capitalize">
                            {user.schoolRole.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>{user.department || '-'}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={user.status === 'error' ? 'destructive' : 'default'}
                            className="capitalize"
                          >
                            {user.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Progress Tab */}
        <TabsContent value="progress" className="space-y-6">
          {selectedJob && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <RefreshCw className={`h-5 w-5 ${selectedJob.status === 'processing' ? 'animate-spin' : ''}`} />
                    Import Progress
                  </CardTitle>
                  <CardDescription>
                    {selectedJob.filename} - Started {new Date(selectedJob.createdAt).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{selectedJob.totalUsers}</div>
                      <div className="text-sm text-gray-600">Total Users</div>
                    </div>
                    
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">{selectedJob.processedUsers}</div>
                      <div className="text-sm text-gray-600">Processed</div>
                    </div>
                    
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{selectedJob.successfulUsers}</div>
                      <div className="text-sm text-gray-600">Successful</div>
                    </div>
                    
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{selectedJob.failedUsers}</div>
                      <div className="text-sm text-gray-600">Failed</div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Progress</span>
                      <span>{Math.round(uploadProgress)}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-3" />
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge 
                      variant={
                        selectedJob.status === 'completed' ? 'default' :
                        selectedJob.status === 'failed' ? 'destructive' :
                        'secondary'
                      }
                      className="capitalize"
                    >
                      {selectedJob.status}
                    </Badge>
                    {selectedJob.status === 'processing' && (
                      <span className="text-sm text-gray-600">Importing users...</span>
                    )}
                  </div>
                </CardContent>
              </Card>

              {selectedJob.errors.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="h-5 w-5" />
                      Import Errors ({selectedJob.errors.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-64 overflow-auto">
                      {selectedJob.errors.map((error, index) => (
                        <Alert key={index} variant="destructive">
                          <AlertTitle>Row {error.row}: {error.email}</AlertTitle>
                          <AlertDescription>{error.error}</AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Import History
              </CardTitle>
              <CardDescription>
                View previous bulk import jobs and their results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {importJobs.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">No Import History</h3>
                  <p className="text-gray-500">You haven't run any bulk imports yet.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {importJobs.map((job) => (
                    <Card key={job.id} className="border">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">{job.filename}</h4>
                            <p className="text-sm text-gray-600">
                              {new Date(job.createdAt).toLocaleString()}
                              {job.completedAt && ` - ${new Date(job.completedAt).toLocaleString()}`}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant={
                                job.status === 'completed' ? 'default' :
                                job.status === 'failed' ? 'destructive' :
                                'secondary'
                              }
                              className="capitalize"
                            >
                              {job.status}
                            </Badge>
                            
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedJob(job);
                                setActiveTab('progress');
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-4 gap-4 mt-3 text-sm">
                          <div>
                            <span className="text-gray-500">Total:</span> {job.totalUsers}
                          </div>
                          <div>
                            <span className="text-gray-500">Processed:</span> {job.processedUsers}
                          </div>
                          <div>
                            <span className="text-gray-500">Success:</span> {job.successfulUsers}
                          </div>
                          <div>
                            <span className="text-gray-500">Failed:</span> {job.failedUsers}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};