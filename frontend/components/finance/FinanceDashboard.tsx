// =====================================================
// Finance Dashboard Component
// File: frontend/components/finance/FinanceDashboard.tsx
// =====================================================

"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  DollarSign, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  Download, 
  Send, 
  Plus, 
  CreditCard,
  Clock,
  Users,
  FileText,
  Wallet
} from "lucide-react"

import { financeApi, FinanceDashboard as FinanceDashboardType } from "@/lib/finance-api"
import { useSchoolContext } from "@/hooks/useSchoolContext"
import { useAuth } from "@/hooks/useAuth"

interface FinanceDashboardProps {
  academicYearId: string
}

export default function FinanceDashboard({ academicYearId }: FinanceDashboardProps) {
  const { user } = useAuth()
  const schoolContext = useSchoolContext()
  const [selectedPeriod, setSelectedPeriod] = useState<'current' | 'ytd'>('current')

  // Fetch dashboard data
  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['finance-dashboard', academicYearId],
    queryFn: () => financeApi.getFinanceDashboard(academicYearId),
    enabled: !!academicYearId,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-8 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error || !dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to load dashboard</h3>
          <p className="text-gray-600 mb-4">There was an error loading the finance dashboard.</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    )
  }

  const currentData = {
    invoiced: dashboard.current_term_invoiced,
    collected: dashboard.current_term_collected,
    outstanding: dashboard.current_term_outstanding,
    rate: dashboard.current_term_collection_rate
  }

  const ytdData = {
    invoiced: dashboard.year_to_date_invoiced,
    collected: dashboard.year_to_date_collected,
    outstanding: dashboard.year_to_date_outstanding,
    rate: dashboard.year_to_date_collection_rate
  }

  const displayData = selectedPeriod === 'current' ? currentData : ytdData

  const formatCurrency = (amount: number) => {
    return schoolContext?.formatCurrency(amount) || `$${amount.toLocaleString()}`
  }

  const getCollectionRateColor = (rate: number) => {
    if (rate >= 90) return "text-green-600"
    if (rate >= 70) return "text-yellow-600"
    return "text-red-600"
  }

  const getCollectionRateBadge = (rate: number) => {
    if (rate >= 90) return "bg-green-100 text-green-800"
    if (rate >= 70) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  return (
    <div className="space-y-6">
      {/* Period Selection */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Financial Overview</h2>
          <p className="text-muted-foreground">
            Track collection performance and financial health
          </p>
        </div>
        <Tabs value={selectedPeriod} onValueChange={(value) => setSelectedPeriod(value as 'current' | 'ytd')}>
          <TabsList>
            <TabsTrigger value="current">Current Term</TabsTrigger>
            <TabsTrigger value="ytd">Year to Date</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Invoiced</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(displayData.invoiced)}</div>
            <p className="text-xs text-muted-foreground">
              {selectedPeriod === 'current' ? 'Current term' : 'Academic year'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Collected</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(displayData.collected)}</div>
            <p className="text-xs text-muted-foreground">
              {Math.round(displayData.rate)}% of invoiced amount
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(displayData.outstanding)}</div>
            <p className="text-xs text-muted-foreground">
              {dashboard.overdue_invoices_count} overdue invoices
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Rate</CardTitle>
            <TrendingUp className={`h-4 w-4 ${getCollectionRateColor(displayData.rate)}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getCollectionRateColor(displayData.rate)}`}>
              {Math.round(displayData.rate)}%
            </div>
            <Badge className={`text-xs ${getCollectionRateBadge(displayData.rate)}`}>
              {displayData.rate >= 90 ? 'Excellent' : displayData.rate >= 70 ? 'Good' : 'Needs Attention'}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Collection Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Collection Progress</CardTitle>
          <CardDescription>
            Visual representation of fee collection performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Payment Collection</span>
              <span className="text-sm text-muted-foreground">
                {formatCurrency(displayData.collected)} / {formatCurrency(displayData.invoiced)}
              </span>
            </div>
            <Progress value={displayData.rate} className="h-3" />
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Collected:</span>
                <span className="font-medium text-green-600">{formatCurrency(displayData.collected)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Outstanding:</span>
                <span className="font-medium text-red-600">{formatCurrency(displayData.outstanding)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity and Alerts */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Payments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Payments</CardTitle>
              <CardDescription>Latest payments received</CardDescription>
            </div>
            <Badge variant="outline" className="ml-auto">
              {dashboard.recent_payments.length} new
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboard.recent_payments.length === 0 ? (
                <div className="text-center py-8">
                  <Wallet className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No recent payments</p>
                </div>
              ) : (
                dashboard.recent_payments.slice(0, 5).map((payment) => (
                  <div key={payment.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <CreditCard className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{payment.student_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {payment.payment_method?.name} • {new Date(payment.payment_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatCurrency(payment.amount)}</p>
                      <Badge 
                        variant={payment.status === 'completed' ? 'default' : 'secondary'} 
                        className="text-xs"
                      >
                        {payment.status}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions & Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common finance tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" size="sm" className="justify-start">
                <Plus className="mr-2 h-4 w-4" />
                Record Payment
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <FileText className="mr-2 h-4 w-4" />
                Generate Invoice
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <Send className="mr-2 h-4 w-4" />
                Send Reminders
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <Download className="mr-2 h-4 w-4" />
                Export Report
              </Button>
            </div>

            {/* Alerts */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Attention Required</h4>
              
              {dashboard.overdue_invoices_count > 0 && (
                <div className="flex items-center space-x-2 p-2 bg-red-50 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm text-red-800">
                    {dashboard.overdue_invoices_count} overdue invoices
                  </span>
                </div>
              )}

              {dashboard.pending_payments_count > 0 && (
                <div className="flex items-center space-x-2 p-2 bg-yellow-50 rounded-lg">
                  <Clock className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm text-yellow-800">
                    {dashboard.pending_payments_count} pending payments
                  </span>
                </div>
              )}

              {displayData.rate < 70 && (
                <div className="flex items-center space-x-2 p-2 bg-orange-50 rounded-lg">
                  <TrendingUp className="h-4 w-4 text-orange-600" />
                  <span className="text-sm text-orange-800">
                    Low collection rate ({Math.round(displayData.rate)}%)
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payment Method Breakdown */}
      {dashboard.payment_method_breakdown.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Payment Methods</CardTitle>
            <CardDescription>Breakdown of payments by method</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboard.payment_method_breakdown.map((method) => (
                <div key={method.method} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium">{method.method}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{formatCurrency(method.amount)}</p>
                    <p className="text-xs text-muted-foreground">
                      {method.count} transactions ({method.percentage}%)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}