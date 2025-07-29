"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Download, Play, Plus, Search, Filter, Calendar, Eye, Edit, Trash2 } from 'lucide-react';
import { useSchoolContext } from '@/hooks/useSchoolContext';

interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  report_type: string;
  is_public: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface ReportExecution {
  id: string;
  template_id: string;
  status: string;
  execution_date: string;
  parameters: Record<string, any>;
  row_count?: number;
  file_path?: string;
  download_url?: string;
}

interface ReportTemplateCreate {
  name: string;
  description?: string;
  category: string;
  report_type: string;
  data_sources: Array<Record<string, any>>;
  filters: Record<string, any>;
  columns: Array<Record<string, any>>;
  charts: Array<Record<string, any>>;
  is_public: boolean;
  allowed_roles: string[];
}

const ReportTemplateForm: React.FC<{
  onSubmit: (template: ReportTemplateCreate) => void;
  onCancel: () => void;
  initialData?: Partial<ReportTemplateCreate>;
}> = ({ onSubmit, onCancel, initialData }) => {
  const [formData, setFormData] = useState<ReportTemplateCreate>({
    name: '',
    description: '',
    category: 'academic',
    report_type: 'table',
    data_sources: [{ source: 'sis.students', joins: [] }],
    filters: {},
    columns: [],
    charts: [],
    is_public: false,
    allowed_roles: ['admin'],
    ...initialData
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Report Name</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter report name"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select
            value={formData.category}
            onValueChange={(value) => setFormData({ ...formData, category: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="academic">Academic</SelectItem>
              <SelectItem value="financial">Financial</SelectItem>
              <SelectItem value="administrative">Administrative</SelectItem>
              <SelectItem value="analytics">Analytics</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Describe what this report shows"
          rows={3}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="report_type">Report Type</Label>
          <Select
            value={formData.report_type}
            onValueChange={(value) => setFormData({ ...formData, report_type: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="table">Table</SelectItem>
              <SelectItem value="chart">Chart</SelectItem>
              <SelectItem value="dashboard">Dashboard</SelectItem>
              <SelectItem value="pdf">PDF Report</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Visibility</Label>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_public"
              checked={formData.is_public}
              onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <Label htmlFor="is_public" className="text-sm">Make this report public</Label>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">
          Create Report
        </Button>
      </div>
    </form>
  );
};

const ReportExecutionHistory: React.FC<{
  executions: ReportExecution[];
  onDownload: (execution: ReportExecution) => void;
}> = ({ executions, onDownload }) => {
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      running: { color: 'bg-blue-100 text-blue-800', label: 'Running' },
      completed: { color: 'bg-green-100 text-green-800', label: 'Completed' },
      failed: { color: 'bg-red-100 text-red-800', label: 'Failed' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Execution Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Rows</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {executions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  No executions found
                </TableCell>
              </TableRow>
            ) : (
              executions.map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell>
                    {new Date(execution.execution_date).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(execution.status)}
                  </TableCell>
                  <TableCell>
                    {execution.row_count ? execution.row_count.toLocaleString() : '-'}
                  </TableCell>
                  <TableCell>
                    -
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {execution.status === 'completed' && execution.download_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onDownload(execution)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export const ReportsManagement: React.FC = () => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [executions, setExecutions] = useState<ReportExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const { schoolContext } = useSchoolContext();

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/reports/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch report templates');
      }

      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    }
  };

  const fetchExecutions = async () => {
    try {
      const response = await fetch('/api/v1/reports/executions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch report executions');
      }

      const data = await response.json();
      setExecutions(data);
    } catch (err) {
      console.error('Error fetching executions:', err);
    }
  };

  const createTemplate = async (templateData: ReportTemplateCreate) => {
    try {
      const response = await fetch('/api/v1/reports/templates', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(templateData)
      });

      if (!response.ok) {
        throw new Error('Failed to create report template');
      }

      setShowCreateDialog(false);
      await fetchTemplates();
    } catch (err) {
      console.error('Error creating template:', err);
      setError(err instanceof Error ? err.message : 'Failed to create template');
    }
  };

  const executeReport = async (templateId: string) => {
    try {
      const response = await fetch('/api/v1/reports/execute', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template_id: templateId,
          parameters: {},
          filters: {},
          output_format: 'json'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to execute report');
      }

      await fetchExecutions();
    } catch (err) {
      console.error('Error executing report:', err);
      setError(err instanceof Error ? err.message : 'Failed to execute report');
    }
  };

  const downloadReport = async (execution: ReportExecution) => {
    if (execution.download_url) {
      window.open(execution.download_url, '_blank');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTemplates(), fetchExecutions()]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Reports Management</h1>
          <p className="text-muted-foreground">
            Create, manage, and execute custom reports for {schoolContext?.school_name || 'your school'}
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Report
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Report Template</DialogTitle>
              <DialogDescription>
                Define a new report template that can be executed with different parameters.
              </DialogDescription>
            </DialogHeader>
            <ReportTemplateForm
              onSubmit={createTemplate}
              onCancel={() => setShowCreateDialog(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="templates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="templates">Report Templates</TabsTrigger>
          <TabsTrigger value="executions">Execution History</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search reports..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="academic">Academic</SelectItem>
                <SelectItem value="financial">Financial</SelectItem>
                <SelectItem value="administrative">Administrative</SelectItem>
                <SelectItem value="analytics">Analytics</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Templates Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.length === 0 ? (
              <div className="col-span-full">
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Reports Found</h3>
                    <p className="text-muted-foreground text-center mb-4">
                      {searchTerm || selectedCategory !== 'all'
                        ? 'No reports match your search criteria.'
                        : 'Get started by creating your first report template.'}
                    </p>
                    <Button onClick={() => setShowCreateDialog(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create Report
                    </Button>
                  </CardContent>
                </Card>
              </div>
            ) : (
              filteredTemplates.map((template) => (
                <Card key={template.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline">{template.category}</Badge>
                          <Badge variant="outline">{template.report_type}</Badge>
                          {template.is_public && (
                            <Badge className="bg-blue-100 text-blue-800">Public</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    {template.description && (
                      <CardDescription>
                        {template.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">
                        Created {new Date(template.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          onClick={() => executeReport(template.id)}
                        >
                          <Play className="h-4 w-4 mr-1" />
                          Run
                        </Button>
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Report Executions</CardTitle>
              <CardDescription>
                View and download completed reports
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ReportExecutionHistory
                executions={executions}
                onDownload={downloadReport}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ReportsManagement;