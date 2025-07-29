// =====================================================
// Real-time Progress Tracker Component
// File: frontend/components/progress/ProgressTracker.tsx
// =====================================================

'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, wsManager } from '@/lib/api';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Play,
  Pause,
  Square,
  Eye,
  RefreshCw,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';

interface ProgressOperation {
  operation_id: string;
  operation_type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_step: number;
  total_steps: number;
  started_at: string;
  estimated_completion?: string;
  elapsed_time: number;
  current_task?: string;
  processed_items: number;
  total_items: number;
  successful_items: number;
  failed_items: number;
  user_id: string;
  school_id?: string;
  metadata: Record<string, any>;
}

interface BulkOperationProgress {
  operation_id: string;
  operation_type: string;
  status: string;
  total_batches: number;
  completed_batches: number;
  current_batch: number;
  batch_size: number;
  total_items: number;
  processed_items: number;
  successful_items: number;
  failed_items: number;
  progress_percentage: number;
  items_per_second: number;
  estimated_completion?: string;
  errors: Array<any>;
  started_at: string;
  last_updated: string;
}

interface ProgressTrackerProps {
  operationIds?: string[];
  showAllOperations?: boolean;
  autoRefresh?: boolean;
  className?: string;
}

export function ProgressTracker({
  operationIds = [],
  showAllOperations = false,
  autoRefresh = true,
  className
}: ProgressTrackerProps) {
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null);
  const [realTimeUpdates, setRealTimeUpdates] = useState<Record<string, ProgressOperation>>({});

  // Fetch operations list
  const { data: operations, isLoading, refetch } = useQuery({
    queryKey: ['progress-operations', operationIds, showAllOperations],
    queryFn: async () => {
      if (showAllOperations) {
        const response = await api.get('/api/v1/realtime/operations');
        return response.data as ProgressOperation[];
      } else if (operationIds.length > 0) {
        const operations = await Promise.all(
          operationIds.map(async (id) => {
            try {
              const response = await api.get(`/api/v1/realtime/operations/${id}`);
              return response.data.progress as ProgressOperation;
            } catch (error) {
              console.error(`Failed to fetch operation ${id}:`, error);
              return null;
            }
          })
        );
        return operations.filter(op => op !== null);
      }
      return [];
    },
    refetchInterval: autoRefresh ? 5000 : false, // Refetch every 5 seconds if auto-refresh enabled
    enabled: showAllOperations || operationIds.length > 0,
  });

  // Fetch detailed operation info
  const { data: operationDetails } = useQuery({
    queryKey: ['operation-details', selectedOperation],
    queryFn: async () => {
      if (!selectedOperation) return null;
      const response = await api.get(`/api/v1/realtime/operations/${selectedOperation}`);
      return response.data;
    },
    enabled: !!selectedOperation,
  });

  // Set up WebSocket subscriptions for real-time updates
  useEffect(() => {
    const allOperationIds = operations?.map(op => op.operation_id) || [];
    const targetIds = operationIds.length > 0 ? operationIds : allOperationIds;
    
    if (targetIds.length > 0) {
      wsManager.subscribe(targetIds);
    }

    // Listen for progress updates
    const handleProgressUpdate = (event: CustomEvent) => {
      const progressData = event.detail;
      if (progressData.operation_id) {
        setRealTimeUpdates(prev => ({
          ...prev,
          [progressData.operation_id]: progressData
        }));
      }
    };

    window.addEventListener('progress-update', handleProgressUpdate as EventListener);

    return () => {
      if (targetIds.length > 0) {
        wsManager.unsubscribe(targetIds);
      }
      window.removeEventListener('progress-update', handleProgressUpdate as EventListener);
    };
  }, [operations, operationIds]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'in_progress':
        return <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'cancelled':
        return <Square className="w-4 h-4 text-gray-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatOperationType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const cancelOperation = async (operationId: string) => {
    try {
      await api.delete(`/api/v1/realtime/operations/${operationId}/cancel`);
      toast.success('Operation cancelled');
      refetch();
    } catch (error) {
      toast.error('Failed to cancel operation');
    }
  };

  // Merge real-time updates with static data
  const mergedOperations = operations?.map(op => ({
    ...op,
    ...(realTimeUpdates[op.operation_id] || {})
  })) || [];

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Loading operations...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (mergedOperations.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center">
          <Zap className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">No operations to track</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Progress Tracker</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </CardTitle>
        <CardDescription>
          Real-time tracking of ongoing operations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mergedOperations.map((operation) => (
            <div
              key={operation.operation_id}
              className="p-4 border rounded-lg space-y-3"
            >
              {/* Operation Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(operation.status)}
                  <div>
                    <h4 className="font-medium">{formatOperationType(operation.operation_type)}</h4>
                    <p className="text-sm text-gray-500">
                      Started {formatDateTime(operation.started_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(operation.status)}>
                    {operation.status.replace('_', ' ')}
                  </Badge>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedOperation(operation.operation_id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Operation Details</DialogTitle>
                        <DialogDescription>
                          Detailed information about the operation
                        </DialogDescription>
                      </DialogHeader>
                      {operationDetails && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm font-medium">Operation ID</label>
                              <p className="text-sm text-gray-600 font-mono">
                                {operationDetails.progress?.operation_id}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm font-medium">Type</label>
                              <p className="text-sm text-gray-600">
                                {formatOperationType(operationDetails.progress?.operation_type)}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm font-medium">Progress</label>
                              <p className="text-sm text-gray-600">
                                {operationDetails.progress?.current_step} / {operationDetails.progress?.total_steps}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm font-medium">Success Rate</label>
                              <p className="text-sm text-gray-600">
                                {operationDetails.progress?.successful_items} / {operationDetails.progress?.total_items}
                              </p>
                            </div>
                          </div>
                          
                          {operationDetails.bulk_progress && (
                            <div>
                              <h4 className="font-medium mb-2">Bulk Operation Details</h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <label className="text-sm font-medium">Batches</label>
                                  <p className="text-sm text-gray-600">
                                    {operationDetails.bulk_progress.completed_batches} / {operationDetails.bulk_progress.total_batches}
                                  </p>
                                </div>
                                <div>
                                  <label className="text-sm font-medium">Processing Rate</label>
                                  <p className="text-sm text-gray-600">
                                    {operationDetails.bulk_progress.items_per_second.toFixed(2)} items/sec
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}

                          {operationDetails.progress?.metadata && Object.keys(operationDetails.progress.metadata).length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">Metadata</h4>
                              <pre className="text-xs bg-gray-100 p-2 rounded">
                                {JSON.stringify(operationDetails.progress.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                  {operation.status === 'in_progress' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => cancelOperation(operation.operation_id)}
                    >
                      <Square className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>{operation.current_task || 'Processing...'}</span>
                  <span>{Math.round(operation.progress_percentage)}%</span>
                </div>
                <Progress value={operation.progress_percentage} className="w-full" />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>
                    {operation.processed_items} / {operation.total_items} items
                  </span>
                  <span>
                    Elapsed: {formatDuration(operation.elapsed_time)}
                    {operation.estimated_completion && (
                      <> • ETA: {formatDateTime(operation.estimated_completion)}</>
                    )}
                  </span>
                </div>
              </div>

              {/* Stats */}
              {(operation.successful_items > 0 || operation.failed_items > 0) && (
                <div className="flex space-x-4 text-sm">
                  <span className="text-green-600">
                    ✓ {operation.successful_items} successful
                  </span>
                  {operation.failed_items > 0 && (
                    <span className="text-red-600">
                      ✗ {operation.failed_items} failed
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}