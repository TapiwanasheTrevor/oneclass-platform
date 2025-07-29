"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { DollarSign, TrendingUp, AlertCircle, CheckCircle, Download, Send, Plus, CreditCard } from "lucide-react"

const feeCollections = [
  {
    term: "Term 1 2024",
    expected: 125000,
    collected: 97500,
    outstanding: 27500,
    percentage: 78,
  },
  {
    term: "Term 2 2024",
    expected: 125000,
    collected: 112500,
    outstanding: 12500,
    percentage: 90,
  },
  {
    term: "Term 3 2024",
    expected: 125000,
    collected: 45000,
    outstanding: 80000,
    percentage: 36,
  },
]

const recentPayments = [
  {
    id: "PAY001",
    student: "Tendai Mukamuri",
    amount: 450,
    method: "EcoCash",
    date: "2024-01-15",
    status: "Completed",
  },
  {
    id: "PAY002",
    student: "Chipo Nyathi",
    amount: 450,
    method: "Bank Transfer",
    date: "2024-01-14",
    status: "Completed",
  },
  {
    id: "PAY003",
    student: "Blessing Moyo",
    amount: 225,
    method: "Cash",
    date: "2024-01-14",
    status: "Completed",
  },
  {
    id: "PAY004",
    student: "Rutendo Chikwanha",
    amount: 450,
    method: "Swipe",
    date: "2024-01-13",
    status: "Pending",
  },
]

const outstandingFees = [
  {
    student: "Takudzwa Sibanda",
    grade: "Form 4B",
    amount: 900,
    daysOverdue: 45,
    guardian: "Robert Sibanda",
    phone: "+263 71 345 6789",
  },
  {
    student: "Chipo Nyathi",
    grade: "Form 3B",
    amount: 225,
    daysOverdue: 15,
    guardian: "Mary Nyathi",
    phone: "+263 71 987 6543",
  },
  {
    student: "Farai Dube",
    grade: "Form 2C",
    amount: 450,
    daysOverdue: 30,
    guardian: "James Dube",
    phone: "+263 77 111 2222",
  },
]

export default function FinancePage() {
  const [selectedTerm] = useState("Term 1 2024")

  const currentTerm = feeCollections.find((term) => term.term === selectedTerm)
  const totalExpected = feeCollections.reduce((sum, term) => sum + term.expected, 0)
  const totalCollected = feeCollections.reduce((sum, term) => sum + term.collected, 0)
  const totalOutstanding = feeCollections.reduce((sum, term) => sum + term.outstanding, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Finance & Billing</h1>
          <p className="text-muted-foreground">Manage school finances, fee collection, and billing</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Record Payment
          </Button>
        </div>
      </div>

      {/* Financial Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expected</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalExpected.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">All terms combined</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Collected</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalCollected.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {Math.round((totalCollected / totalExpected) * 100)}% of expected
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalOutstanding.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Requires follow-up</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round((totalCollected / totalExpected) * 100)}%</div>
            <p className="text-xs text-muted-foreground">Overall performance</p>
          </CardContent>
        </Card>
      </div>

      {/* Term-wise Collection */}
      <Card>
        <CardHeader>
          <CardTitle>Fee Collection by Term</CardTitle>
          <CardDescription>Track collection progress across academic terms</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {feeCollections.map((term) => (
            <div key={term.term} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">{term.term}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-muted-foreground">
                    ${term.collected.toLocaleString()} / ${term.expected.toLocaleString()}
                  </span>
                  <Badge
                    variant={term.percentage >= 80 ? "default" : term.percentage >= 60 ? "secondary" : "destructive"}
                  >
                    {term.percentage}%
                  </Badge>
                </div>
              </div>
              <Progress value={term.percentage} className="h-2" />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Payments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Payments</CardTitle>
            <CardDescription>Latest fee payments received</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentPayments.map((payment) => (
                <div key={payment.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{payment.student}</p>
                      <p className="text-xs text-muted-foreground">
                        {payment.method} • {payment.date}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">${payment.amount}</p>
                    <Badge variant={payment.status === "Completed" ? "default" : "secondary"} className="text-xs">
                      {payment.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Outstanding Fees */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Outstanding Fees</CardTitle>
              <CardDescription>Students with overdue payments</CardDescription>
            </div>
            <Button size="sm">
              <Send className="mr-2 h-4 w-4" />
              Send Reminders
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {outstandingFees.map((fee, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{fee.student}</p>
                    <p className="text-xs text-muted-foreground">
                      {fee.grade} • {fee.guardian}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">${fee.amount}</p>
                    <Badge variant="destructive" className="text-xs">
                      {fee.daysOverdue} days overdue
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
