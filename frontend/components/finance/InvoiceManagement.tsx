// =====================================================
// Invoice Management Component
// File: frontend/components/finance/InvoiceManagement.tsx
// =====================================================

"use client"

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { toast } from "@/components/ui/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { 
  Search, 
  Plus, 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Send, 
  Download, 
  Filter,
  CalendarIcon,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  Users,
  Loader2
} from "lucide-react"

import { financeApi, Invoice, FeeStructure } from "@/lib/finance-api"
import { useSchoolContext } from "@/hooks/useSchoolContext"
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"
import { format } from "date-fns"

interface InvoiceManagementProps {
  academicYearId: string
}

export default function InvoiceManagement({ academicYearId }: InvoiceManagementProps) {
  const { user } = useAuth()
  const schoolContext = useSchoolContext()
  const queryClient = useQueryClient()

  // State management
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState<string>("all")
  const [selectedGrade, setSelectedGrade] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showBulkDialog, setShowBulkDialog] = useState(false)
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([])

  // Form state
  const [createForm, setCreateForm] = useState({
    student_id: "",
    fee_structure_id: "",
    due_date: null as Date | null,
    term_id: "",
    notes: ""
  })

  const [bulkForm, setBulkForm] = useState({
    fee_structure_id: "",
    due_date: null as Date | null,
    term_id: "",
    student_ids: [] as string[],
    grade_levels: [] as number[],
    class_ids: [] as string[]
  })

  // Fetch invoices
  const { data: invoicesData, isLoading: isLoadingInvoices } = useQuery({
    queryKey: ['invoices', academicYearId, page, pageSize, selectedStatus, selectedGrade, searchTerm],
    queryFn: () => financeApi.getInvoices({
      page,
      page_size: pageSize,
      academic_year_id: academicYearId,
      payment_status: selectedStatus !== 'all' ? selectedStatus : undefined,
      grade_level: selectedGrade !== 'all' ? parseInt(selectedGrade) : undefined,
      search: searchTerm || undefined
    }),
    enabled: !!academicYearId,
  })

  // Fetch fee structures for dropdowns
  const { data: feeStructures = [] } = useQuery({
    queryKey: ['fee-structures', academicYearId],
    queryFn: () => financeApi.getFeeStructures({ academic_year_id: academicYearId, status: 'active' }),
    enabled: !!academicYearId,
  })

  // Create invoice mutation
  const createInvoiceMutation = useMutation({
    mutationFn: financeApi.createInvoice,
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Invoice created successfully",
      })
      setShowCreateDialog(false)
      setCreateForm({
        student_id: "",
        fee_structure_id: "",
        due_date: null,
        term_id: "",
        notes: ""
      })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to create invoice",
        variant: "destructive",
      })
    }
  })

  // Bulk generate invoices mutation
  const bulkGenerateMutation = useMutation({
    mutationFn: financeApi.bulkGenerateInvoices,
    onSuccess: (data) => {
      toast({
        title: "Success",
        description: `Generated ${data.total_invoices_generated} invoices for ${data.total_students_processed} students`,
      })
      setShowBulkDialog(false)
      setBulkForm({
        fee_structure_id: "",
        due_date: null,
        term_id: "",
        student_ids: [],
        grade_levels: [],
        class_ids: []
      })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to generate invoices",
        variant: "destructive",
      })
    }
  })

  // Send invoice mutation
  const sendInvoiceMutation = useMutation({
    mutationFn: financeApi.sendInvoice,
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Invoice sent successfully",
      })
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to send invoice",
        variant: "destructive",
      })
    }
  })

  const formatCurrency = (amount: number) => {
    return schoolContext?.formatCurrency(amount) || `$${amount.toLocaleString()}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return "bg-green-100 text-green-800"
      case 'partial':
        return "bg-blue-100 text-blue-800"
      case 'overdue':
        return "bg-red-100 text-red-800"
      case 'pending':
        return "bg-yellow-100 text-yellow-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'partial':
        return <Clock className="h-4 w-4 text-blue-600" />
      case 'overdue':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-600" />
    }
  }

  const handleCreateInvoice = () => {
    if (!createForm.student_id || !createForm.fee_structure_id || !createForm.due_date) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    createInvoiceMutation.mutate({
      student_id: createForm.student_id,
      fee_structure_id: createForm.fee_structure_id,
      due_date: format(createForm.due_date, 'yyyy-MM-dd'),
      academic_year_id: academicYearId,
      term_id: createForm.term_id || undefined,
      notes: createForm.notes || undefined
    })
  }

  const handleBulkGenerate = () => {
    if (!bulkForm.fee_structure_id || !bulkForm.due_date) {
      toast({
        title: "Error",
        description: "Please select fee structure and due date",
        variant: "destructive",
      })
      return
    }

    if (bulkForm.student_ids.length === 0 && bulkForm.grade_levels.length === 0 && bulkForm.class_ids.length === 0) {
      toast({
        title: "Error",
        description: "Please select students, grade levels, or classes",
        variant: "destructive",
      })
      return
    }

    bulkGenerateMutation.mutate({
      fee_structure_id: bulkForm.fee_structure_id,
      due_date: format(bulkForm.due_date, 'yyyy-MM-dd'),
      academic_year_id: academicYearId,
      term_id: bulkForm.term_id || undefined,
      student_ids: bulkForm.student_ids.length > 0 ? bulkForm.student_ids : undefined,
      grade_levels: bulkForm.grade_levels.length > 0 ? bulkForm.grade_levels : undefined,
      class_ids: bulkForm.class_ids.length > 0 ? bulkForm.class_ids : undefined
    })
  }

  const handleSendInvoice = (invoiceId: string) => {
    sendInvoiceMutation.mutate(invoiceId)
  }

  const handleSelectInvoice = (invoiceId: string) => {
    setSelectedInvoices(prev => 
      prev.includes(invoiceId) 
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    )
  }

  const handleSelectAll = () => {
    if (selectedInvoices.length === invoicesData?.invoices.length) {
      setSelectedInvoices([])
    } else {
      setSelectedInvoices(invoicesData?.invoices.map(invoice => invoice.id) || [])
    }
  }

  if (isLoadingInvoices) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Invoice Management</h2>
          <p className="text-muted-foreground">
            Create, manage, and track student fee invoices
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Users className="mr-2 h-4 w-4" />
                Bulk Generate
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Bulk Generate Invoices</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="fee-structure">Fee Structure *</Label>
                    <Select
                      value={bulkForm.fee_structure_id}
                      onValueChange={(value) => setBulkForm(prev => ({ ...prev, fee_structure_id: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select fee structure" />
                      </SelectTrigger>
                      <SelectContent>
                        {feeStructures.map((structure) => (
                          <SelectItem key={structure.id} value={structure.id}>
                            {structure.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="due-date">Due Date *</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant={"outline"}
                          className={cn(
                            "w-full justify-start text-left font-normal",
                            !bulkForm.due_date && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {bulkForm.due_date ? format(bulkForm.due_date, "PPP") : <span>Pick a date</span>}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={bulkForm.due_date}
                          onSelect={(date) => setBulkForm(prev => ({ ...prev, due_date: date }))}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Target Students (select at least one)</Label>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="text-sm">Grade Levels</Label>
                      <div className="space-y-1">
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((grade) => (
                          <div key={grade} className="flex items-center space-x-2">
                            <Checkbox
                              id={`grade-${grade}`}
                              checked={bulkForm.grade_levels.includes(grade)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setBulkForm(prev => ({ 
                                    ...prev, 
                                    grade_levels: [...prev.grade_levels, grade] 
                                  }))
                                } else {
                                  setBulkForm(prev => ({ 
                                    ...prev, 
                                    grade_levels: prev.grade_levels.filter(g => g !== grade) 
                                  }))
                                }
                              }}
                            />
                            <Label htmlFor={`grade-${grade}`} className="text-sm">
                              {schoolContext?.getGradeDisplay(grade) || `Grade ${grade}`}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowBulkDialog(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleBulkGenerate}
                    disabled={bulkGenerateMutation.isPending}
                  >
                    {bulkGenerateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Generate Invoices
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Create Invoice
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Invoice</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="student">Student *</Label>
                  <Input
                    id="student"
                    placeholder="Search and select student..."
                    value={createForm.student_id}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, student_id: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fee-structure">Fee Structure *</Label>
                  <Select
                    value={createForm.fee_structure_id}
                    onValueChange={(value) => setCreateForm(prev => ({ ...prev, fee_structure_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select fee structure" />
                    </SelectTrigger>
                    <SelectContent>
                      {feeStructures.map((structure) => (
                        <SelectItem key={structure.id} value={structure.id}>
                          {structure.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="due-date">Due Date *</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !createForm.due_date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {createForm.due_date ? format(createForm.due_date, "PPP") : <span>Pick a date</span>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={createForm.due_date}
                        onSelect={(date) => setCreateForm(prev => ({ ...prev, due_date: date }))}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    placeholder="Optional notes for the invoice..."
                    value={createForm.notes}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, notes: e.target.value }))}
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleCreateInvoice}
                    disabled={createInvoiceMutation.isPending}
                  >
                    {createInvoiceMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create Invoice
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{invoicesData?.total_count || 0}</div>
            <p className="text-xs text-muted-foreground">This academic year</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paid Invoices</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {invoicesData?.invoices.filter(i => i.payment_status === 'paid').length || 0}
            </div>
            <p className="text-xs text-muted-foreground">Fully paid</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {invoicesData?.invoices.filter(i => i.payment_status === 'overdue').length || 0}
            </div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(invoicesData?.invoices.reduce((sum, i) => sum + i.total_amount, 0) || 0)}
            </div>
            <p className="text-xs text-muted-foreground">Outstanding amount</p>
          </CardContent>
        </Card>
      </div>

      {/* Invoices Table */}
      <Card>
        <CardHeader>
          <CardTitle>Invoices</CardTitle>
          <CardDescription>Manage and track all student invoices</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex items-center space-x-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search invoices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedGrade} onValueChange={setSelectedGrade}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by grade" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Grades</SelectItem>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((grade) => (
                  <SelectItem key={grade} value={grade.toString()}>
                    {schoolContext?.getGradeDisplay(grade) || `Grade ${grade}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedInvoices.length === invoicesData?.invoices.length}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Student</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Paid</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoicesData?.invoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedInvoices.includes(invoice.id)}
                        onCheckedChange={() => handleSelectInvoice(invoice.id)}
                      />
                    </TableCell>
                    <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{invoice.student_name}</div>
                        <div className="text-sm text-muted-foreground">{invoice.student_number}</div>
                      </div>
                    </TableCell>
                    <TableCell>{invoice.grade_level}</TableCell>
                    <TableCell>{format(new Date(invoice.due_date), 'dd/MM/yyyy')}</TableCell>
                    <TableCell>{formatCurrency(invoice.total_amount)}</TableCell>
                    <TableCell>{formatCurrency(invoice.paid_amount)}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(invoice.payment_status)}>
                        {getStatusIcon(invoice.payment_status)}
                        <span className="ml-1">{invoice.payment_status}</span>
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit Invoice
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleSendInvoice(invoice.id)}>
                            <Send className="mr-2 h-4 w-4" />
                            Send to Parent
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Download className="mr-2 h-4 w-4" />
                            Download PDF
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            Cancel Invoice
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {invoicesData && invoicesData.total_pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, invoicesData.total_count)} of {invoicesData.total_count} invoices
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= invoicesData.total_pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}