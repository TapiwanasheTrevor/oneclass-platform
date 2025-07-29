"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, Minus, Users, GraduationCap, DollarSign, Activity } from 'lucide-react';
import { useSchoolContext } from '@/hooks/useSchoolContext';

interface MetricValue {
  value: number | string;
  previous_value?: number | string;
  change?: number;
  change_percentage?: number;
  trend?: 'up' | 'down' | 'stable';
  format: 'number' | 'percentage' | 'currency' | 'text';
}

interface ChartData {
  type: string;
  title: string;
  data: any[];
  labels?: string[];
  datasets?: any[];
  options?: any;
}

interface StudentMetrics {
  total_students: MetricValue;
  active_students: MetricValue;
  new_enrollments: MetricValue;
  withdrawals: MetricValue;
  attendance_rate: MetricValue;
  enrollment_trend: ChartData;
}

interface AcademicMetrics {
  average_grade: MetricValue;
  pass_rate: MetricValue;
  attendance_rate: MetricValue;
  assignment_completion: MetricValue;
  grade_distribution: ChartData;
  subject_performance: ChartData;
}

interface FinancialMetrics {
  total_revenue: MetricValue;
  fees_collected: MetricValue;
  outstanding_fees: MetricValue;
  collection_rate: MetricValue;
  revenue_trend: ChartData;
  fee_breakdown: ChartData;
  payment_methods: ChartData;
}

interface SystemMetrics {
  total_users: MetricValue;
  active_users: MetricValue;
  daily_logins: MetricValue;
  feature_usage: Record<string, MetricValue>;
}

interface AnalyticsData {
  school_id: string;
  period: string;
  start_date: string;
  end_date: string;
  generated_at: string;
  student_metrics: StudentMetrics;
  academic_metrics: AcademicMetrics;
  financial_metrics: FinancialMetrics;
  system_metrics: SystemMetrics;
  insights: Array<{
    type: string;
    title: string;
    message: string;
  }>;
  recommendations: Array<{
    priority: string;
    category: string;
    action: string;
    expected_impact: string;
  }>;
}

type PeriodType = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';

const MetricCard: React.FC<{
  title: string;
  metric: MetricValue;
  icon: React.ReactNode;
  description?: string;
}> = ({ title, metric, icon, description }) => {
  const formatValue = (value: number | string, format: string) => {
    if (typeof value === 'string') return value;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(value);
      case 'percentage':
        return `${value}%`;
      case 'number':
        return new Intl.NumberFormat('en-US').format(value);
      default:
        return value.toString();
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {formatValue(metric.value, metric.format)}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        )}
        {metric.change_percentage !== undefined && (
          <div className={`flex items-center space-x-1 text-xs ${getTrendColor(metric.trend)} mt-1`}>
            {getTrendIcon(metric.trend)}
            <span>
              {metric.change_percentage > 0 ? '+' : ''}{metric.change_percentage.toFixed(1)}%
              {metric.previous_value && ` from ${formatValue(metric.previous_value, metric.format)}`}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const InsightCard: React.FC<{
  insight: {
    type: string;
    title: string;
    message: string;
  }
}> = ({ insight }) => {
  const getInsightColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'alert':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getInsightColor(insight.type)}`}>
      <h4 className="font-semibold text-sm mb-1">{insight.title}</h4>
      <p className="text-sm">{insight.message}</p>
    </div>
  );
};

const RecommendationCard: React.FC<{
  recommendation: {
    priority: string;
    category: string;
    action: string;
    expected_impact: string;
  }
}> = ({ recommendation }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="p-4 rounded-lg border bg-white">
      <div className="flex items-center justify-between mb-2">
        <Badge className={getPriorityColor(recommendation.priority)}>
          {recommendation.priority} priority
        </Badge>
        <Badge variant="outline">{recommendation.category}</Badge>
      </div>
      <h4 className="font-semibold text-sm mb-1">{recommendation.action}</h4>
      <p className="text-sm text-muted-foreground">{recommendation.expected_impact}</p>
    </div>
  );
};

export const AnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<PeriodType>('monthly');
  const { schoolContext } = useSchoolContext();

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/analytics/overview?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics data: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalyticsData(data);
    } catch (err) {
      console.error('Error fetching analytics data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [period]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Analytics</h3>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={fetchAnalyticsData} variant="outline">
            Try Again
          </Button>
        </div>
      </Card>
    );
  }

  if (!analyticsData) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
          <p className="text-muted-foreground">Analytics data is not available at this time.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive insights for {schoolContext?.school_name || 'your school'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={period} onValueChange={(value: PeriodType) => setPeriod(value)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
              <SelectItem value="monthly">Monthly</SelectItem>
              <SelectItem value="quarterly">Quarterly</SelectItem>
              <SelectItem value="yearly">Yearly</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchAnalyticsData} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Students"
          metric={analyticsData.student_metrics.total_students}
          icon={<Users className="h-4 w-4 text-blue-600" />}
          description="Enrolled students"
        />
        <MetricCard
          title="Academic Performance"
          metric={analyticsData.academic_metrics.average_grade}
          icon={<GraduationCap className="h-4 w-4 text-green-600" />}
          description="Average grade"
        />
        <MetricCard
          title="Revenue"
          metric={analyticsData.financial_metrics.total_revenue}
          icon={<DollarSign className="h-4 w-4 text-purple-600" />}
          description="Total fees collected"
        />
        <MetricCard
          title="System Usage"
          metric={analyticsData.system_metrics.active_users}
          icon={<Activity className="h-4 w-4 text-orange-600" />}
          description="Active users"
        />
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="academic">Academic</TabsTrigger>
          <TabsTrigger value="financial">Financial</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <MetricCard
              title="Active Students"
              metric={analyticsData.student_metrics.active_students}
              icon={<Users className="h-4 w-4 text-blue-600" />}
            />
            <MetricCard
              title="Attendance Rate"
              metric={analyticsData.student_metrics.attendance_rate}
              icon={<Activity className="h-4 w-4 text-green-600" />}
            />
            <MetricCard
              title="Pass Rate"
              metric={analyticsData.academic_metrics.pass_rate}
              icon={<GraduationCap className="h-4 w-4 text-purple-600" />}
            />
            <MetricCard
              title="Collection Rate"
              metric={analyticsData.financial_metrics.collection_rate}
              icon={<DollarSign className="h-4 w-4 text-orange-600" />}
            />
            <MetricCard
              title="New Enrollments"
              metric={analyticsData.student_metrics.new_enrollments}
              icon={<Users className="h-4 w-4 text-teal-600" />}
            />
            <MetricCard
              title="Outstanding Fees"
              metric={analyticsData.financial_metrics.outstanding_fees}
              icon={<DollarSign className="h-4 w-4 text-red-600" />}
            />
          </div>
        </TabsContent>

        <TabsContent value="students" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Students"
              metric={analyticsData.student_metrics.total_students}
              icon={<Users className="h-4 w-4 text-blue-600" />}
            />
            <MetricCard
              title="Active Students"
              metric={analyticsData.student_metrics.active_students}
              icon={<Users className="h-4 w-4 text-green-600" />}
            />
            <MetricCard
              title="New Enrollments"
              metric={analyticsData.student_metrics.new_enrollments}
              icon={<Users className="h-4 w-4 text-purple-600" />}
            />
            <MetricCard
              title="Withdrawals"
              metric={analyticsData.student_metrics.withdrawals}
              icon={<Users className="h-4 w-4 text-red-600" />}
            />
          </div>
        </TabsContent>

        <TabsContent value="academic" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Average Grade"
              metric={analyticsData.academic_metrics.average_grade}
              icon={<GraduationCap className="h-4 w-4 text-blue-600" />}
            />
            <MetricCard
              title="Pass Rate"
              metric={analyticsData.academic_metrics.pass_rate}
              icon={<GraduationCap className="h-4 w-4 text-green-600" />}
            />
            <MetricCard
              title="Attendance Rate"
              metric={analyticsData.academic_metrics.attendance_rate}
              icon={<Activity className="h-4 w-4 text-purple-600" />}
            />
            <MetricCard
              title="Assignment Completion"
              metric={analyticsData.academic_metrics.assignment_completion}
              icon={<GraduationCap className="h-4 w-4 text-orange-600" />}
            />
          </div>
        </TabsContent>

        <TabsContent value="financial" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Revenue"
              metric={analyticsData.financial_metrics.total_revenue}
              icon={<DollarSign className="h-4 w-4 text-blue-600" />}
            />
            <MetricCard
              title="Fees Collected"
              metric={analyticsData.financial_metrics.fees_collected}
              icon={<DollarSign className="h-4 w-4 text-green-600" />}
            />
            <MetricCard
              title="Outstanding Fees"
              metric={analyticsData.financial_metrics.outstanding_fees}
              icon={<DollarSign className="h-4 w-4 text-red-600" />}
            />
            <MetricCard
              title="Collection Rate"
              metric={analyticsData.financial_metrics.collection_rate}
              icon={<DollarSign className="h-4 w-4 text-purple-600" />}
            />
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Insights</CardTitle>
                <CardDescription>
                  AI-generated insights based on your data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analyticsData.insights.length > 0 ? (
                  analyticsData.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">
                    No insights available at this time.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
                <CardDescription>
                  Actionable recommendations to improve performance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analyticsData.recommendations.length > 0 ? (
                  analyticsData.recommendations.map((recommendation, index) => (
                    <RecommendationCard key={index} recommendation={recommendation} />
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">
                    No recommendations available at this time.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Footer Information */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-muted-foreground">
            <div>
              Data generated on {new Date(analyticsData.generated_at).toLocaleString()}
            </div>
            <div>
              Period: {analyticsData.period} ({analyticsData.start_date} to {analyticsData.end_date})
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;