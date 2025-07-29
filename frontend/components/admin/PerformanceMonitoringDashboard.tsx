/**
 * Performance Monitoring Dashboard
 * Admin dashboard for monitoring OneClass platform performance
 */

import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, Database, Gauge, RefreshCw, TrendingUp, Users, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

import { useAuth, usePermissions } from '@/hooks/useAuth';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
}

interface PerformanceAlert {
  id: string;
  name: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface CachePerformance {
  current_hit_rate: number;
  avg_hit_rate: number;
  min_hit_rate: number;
  max_hit_rate: number;
  samples: number;
}

interface UserSystemPerformance {
  avg_response_time_ms: number;
  min_response_time_ms: number;
  max_response_time_ms: number;
  p95_response_time_ms: number;
  total_operations: number;
  total_errors: number;
  error_rate: number;
  samples: number;
}

interface SystemResources {
  cpu: {
    avg_usage: number;
    max_usage: number;
  };
  memory: {
    avg_usage: number;
    max_usage: number;
  };
}

interface PerformanceReport {
  report_period: {
    start: string;
    end: string;
    hours: number;
  };
  cache_performance: CachePerformance;
  user_system_performance: UserSystemPerformance;
  system_resources: SystemResources;
  alerts: {
    total_alerts: number;
    by_severity: Record<string, number>;
    active_alerts: number;
    resolved_alerts: number;
  };
  recommendations: string[];
}

interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  monitoring_active: boolean;
  uptime_seconds: number;
  cache_health: any;
  active_alerts: number;
  critical_alerts: number;
  warning_alerts: number;
  timestamp: string;
}

export const PerformanceMonitoringDashboard: React.FC = () => {
  const { token } = useAuth();
  const { isPlatformAdmin } = usePermissions();
  
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [performanceReport, setPerformanceReport] = useState<PerformanceReport | null>(null);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('24');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!isPlatformAdmin) {
      return;
    }
    
    fetchHealthStatus();
    fetchPerformanceReport(parseInt(selectedPeriod));
    fetchAlerts();
  }, [isPlatformAdmin, selectedPeriod]);

  useEffect(() => {
    if (!autoRefresh || !isPlatformAdmin) return;
    
    const interval = setInterval(() => {
      fetchHealthStatus();
      if (Math.random() > 0.7) { // Randomly refresh full report
        fetchPerformanceReport(parseInt(selectedPeriod));
      }
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [autoRefresh, isPlatformAdmin, selectedPeriod]);

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch('/api/v1/health', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const health = await response.json();
        setHealthStatus(health);
      }
    } catch (error) {
      console.error('Error fetching health status:', error);
    }
  };

  const fetchPerformanceReport = async (hours: number) => {
    try {
      setRefreshing(true);
      const response = await fetch(`/api/v1/monitoring/performance-report?hours=${hours}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const report = await response.json();
        setPerformanceReport(report);
      }
    } catch (error) {
      console.error('Error fetching performance report:', error);
      toast.error('Failed to fetch performance report');
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/alerts', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const alertsData = await response.json();
        setAlerts(alertsData.alerts || []);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const handleRefresh = () => {
    fetchHealthStatus();
    fetchPerformanceReport(parseInt(selectedPeriod));
    fetchAlerts();
  };

  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/monitoring/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId ? { ...alert, resolved: true } : alert
        ));
        toast.success('Alert resolved');
      }
    } catch (error) {
      toast.error('Failed to resolve alert');
    }
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / (24 * 3600));
    const hours = Math.floor((seconds % (24 * 3600)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default: return <Activity className="h-5 w-5 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'info': return 'bg-blue-100 text-blue-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isPlatformAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">Access Denied</h3>
          <p className="text-gray-500">You need platform admin privileges to access this dashboard.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 mx-auto animate-spin text-blue-600 mb-4" />
          <p className="text-gray-600">Loading performance data...</p>
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
            <Activity className="h-6 w-6" />
            Performance Monitoring
          </h1>
          <p className="text-gray-600">Monitor OneClass platform performance and health</p>
        </div>
        
        <div className="flex gap-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last Hour</SelectItem>
              <SelectItem value="6">Last 6 Hours</SelectItem>
              <SelectItem value="24">Last 24 Hours</SelectItem>
              <SelectItem value="168">Last Week</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="flex items-center gap-2"
          >
            <Zap className="h-4 w-4" />
            Auto Refresh
          </Button>
        </div>
      </div>

      {/* Overall Health Status */}
      {healthStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(healthStatus.status)}
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-500">Overall Status</p>
                <p className={`text-lg font-semibold ${getStatusColor(healthStatus.status)}`}>
                  {healthStatus.status.toUpperCase()}
                </p>
              </div>
              
              <div className="text-center">
                <p className="text-sm font-medium text-gray-500">Uptime</p>
                <p className="text-lg font-semibold">
                  {formatUptime(healthStatus.uptime_seconds)}
                </p>
              </div>
              
              <div className="text-center">
                <p className="text-sm font-medium text-gray-500">Active Alerts</p>
                <p className="text-lg font-semibold text-red-600">
                  {healthStatus.active_alerts}
                </p>
              </div>
              
              <div className="text-center">
                <p className="text-sm font-medium text-gray-500">Monitoring</p>
                <p className={`text-lg font-semibold ${healthStatus.monitoring_active ? 'text-green-600' : 'text-red-600'}`}>
                  {healthStatus.monitoring_active ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="cache">Cache Performance</TabsTrigger>
          <TabsTrigger value="user-system">User System</TabsTrigger>
          <TabsTrigger value="resources">System Resources</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {performanceReport && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Cache Hit Rate */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {(performanceReport.cache_performance.current_hit_rate * 100).toFixed(1)}%
                  </div>
                  <Progress 
                    value={performanceReport.cache_performance.current_hit_rate * 100} 
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Avg: {(performanceReport.cache_performance.avg_hit_rate * 100).toFixed(1)}%
                  </p>
                </CardContent>
              </Card>

              {/* Response Time */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {performanceReport.user_system_performance.avg_response_time_ms.toFixed(1)}ms
                  </div>
                  <div className="flex items-center mt-2">
                    <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      P95: {performanceReport.user_system_performance.p95_response_time_ms.toFixed(1)}ms
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Error Rate */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {(performanceReport.user_system_performance.error_rate * 100).toFixed(2)}%
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {performanceReport.user_system_performance.total_errors} errors
                  </p>
                </CardContent>
              </Card>

              {/* CPU Usage */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {performanceReport.system_resources.cpu.avg_usage.toFixed(1)}%
                  </div>
                  <Progress 
                    value={performanceReport.system_resources.cpu.avg_usage} 
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Max: {performanceReport.system_resources.cpu.max_usage.toFixed(1)}%
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="cache" className="space-y-4">
          {performanceReport && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Cache Performance Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Current Hit Rate</p>
                    <p className="text-2xl font-semibold">
                      {(performanceReport.cache_performance.current_hit_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">Average Hit Rate</p>
                    <p className="text-2xl font-semibold">
                      {(performanceReport.cache_performance.avg_hit_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">Min Hit Rate</p>
                    <p className="text-2xl font-semibold">
                      {(performanceReport.cache_performance.min_hit_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">Max Hit Rate</p>
                    <p className="text-2xl font-semibold">
                      {(performanceReport.cache_performance.max_hit_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                
                <div className="mt-4">
                  <p className="text-sm text-gray-600">
                    Based on {performanceReport.cache_performance.samples} samples over the selected period.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="user-system" className="space-y-4">
          {performanceReport && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  User System Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
                    <p className="text-2xl font-semibold">
                      {performanceReport.user_system_performance.avg_response_time_ms.toFixed(1)}ms
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">P95 Response Time</p>
                    <p className="text-2xl font-semibold">
                      {performanceReport.user_system_performance.p95_response_time_ms.toFixed(1)}ms
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">Total Operations</p>
                    <p className="text-2xl font-semibold">
                      {performanceReport.user_system_performance.total_operations.toLocaleString()}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-500">Error Rate</p>
                    <p className="text-2xl font-semibold">
                      {(performanceReport.user_system_performance.error_rate * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          {performanceReport && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>CPU Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Average Usage</span>
                        <span className="text-sm">{performanceReport.system_resources.cpu.avg_usage.toFixed(1)}%</span>
                      </div>
                      <Progress value={performanceReport.system_resources.cpu.avg_usage} />
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Peak Usage</span>
                        <span className="text-sm">{performanceReport.system_resources.cpu.max_usage.toFixed(1)}%</span>
                      </div>
                      <Progress value={performanceReport.system_resources.cpu.max_usage} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Memory Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Average Usage</span>
                        <span className="text-sm">{performanceReport.system_resources.memory.avg_usage.toFixed(1)}%</span>
                      </div>
                      <Progress value={performanceReport.system_resources.memory.avg_usage} />
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Peak Usage</span>
                        <span className="text-sm">{performanceReport.system_resources.memory.max_usage.toFixed(1)}%</span>
                      </div>
                      <Progress value={performanceReport.system_resources.memory.max_usage} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Active Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">No Active Alerts</h3>
                  <p className="text-gray-500">All systems are running smoothly.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.filter(alert => !alert.resolved).map((alert) => (
                    <Alert key={alert.id}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle className="flex items-center justify-between">
                        <span>{alert.name}</span>
                        <div className="flex items-center gap-2">
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => resolveAlert(alert.id)}
                          >
                            Resolve
                          </Button>
                        </div>
                      </AlertTitle>
                      <AlertDescription>
                        <p className="mb-2">{alert.message}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Optimization Recommendations */}
          {performanceReport && performanceReport.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gauge className="h-5 w-5" />
                  Optimization Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {performanceReport.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <TrendingUp className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};