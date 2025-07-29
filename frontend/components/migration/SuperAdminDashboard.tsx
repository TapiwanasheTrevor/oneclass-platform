'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Briefcase, DollarSign, Users, CheckCircle, Clock, AlertTriangle, 
  Plus, Search, Filter, MoreHorizontal, Eye, Edit, MessageCircle,
  Calendar, FileText, Database, TrendingUp, User, Phone, Mail,
  Download, Upload, Star, Target, Award, Settings, BarChart3
} from 'lucide-react';

// Types
interface Order {
  id: string;
  schoolName: string;
  package: string;
  price: number;
  status: string;
  progress: number;
  assignedManager: string | null;
  dueDate: string;
  studentCount: number;
  contact: string;
  email: string;
  phone: string;
  orderDate: string;
}

interface TeamMember {
  id: number;
  name: string;
  role: string;
  utilization: number;
  activeProjects: number;
  completedProjects: number;
  rating: number;
}

interface KPIs {
  activeProjects: number;
  monthlyRevenue: number;
  teamUtilization: number;
  successRate: number;
  trends: {
    projects: string;
    revenue: string;
    utilization: string;
    successRate: string;
  };
}

// Mock data - in real app this would come from API
const mockData = {
  kpis: {
    activeProjects: 24,
    monthlyRevenue: 156000,
    teamUtilization: 87,
    successRate: 96,
    trends: {
      projects: '+12%',
      revenue: '+23%',
      utilization: 'Optimal',
      successRate: 'Above target'
    }
  },
  orders: [
    {
      id: 'CP-2025-001',
      schoolName: 'St. Mary\'s High School',
      package: 'Growth Package',
      price: 6500,
      status: 'in_progress',
      progress: 65,
      assignedManager: 'Sarah Moyo',
      dueDate: '2025-08-15',
      studentCount: 450,
      contact: 'John Mukamuri',
      email: 'john@stmarys.edu.zw',
      phone: '+263 77 123 4567',
      orderDate: '2025-07-01'
    },
    {
      id: 'CP-2025-002',
      schoolName: 'Harare International School',
      package: 'Enterprise Package',
      price: 15000,
      status: 'data_migration',
      progress: 35,
      assignedManager: 'Tendai Chigamba',
      dueDate: '2025-08-30',
      studentCount: 1200,
      contact: 'Mary Smith',
      email: 'mary@his.edu.zw',
      phone: '+263 77 987 6543',
      orderDate: '2025-07-10'
    },
    {
      id: 'CP-2025-003',
      schoolName: 'Chitungwiza Primary',
      package: 'Foundation Package',
      price: 2800,
      status: 'pending',
      progress: 0,
      assignedManager: null,
      dueDate: '2025-08-05',
      studentCount: 180,
      contact: 'Peter Banda',
      email: 'peter@chitprimary.edu.zw',
      phone: '+263 77 555 1234',
      orderDate: '2025-07-18'
    }
  ],
  team: [
    {
      id: 1,
      name: 'Sarah Moyo',
      role: 'Senior Migration Manager',
      utilization: 85,
      activeProjects: 3,
      completedProjects: 12,
      rating: 4.8
    },
    {
      id: 2,
      name: 'Tendai Chigamba',
      role: 'Technical Lead',
      utilization: 90,
      activeProjects: 2,
      completedProjects: 8,
      rating: 4.9
    },
    {
      id: 3,
      name: 'Grace Mutindi',
      role: 'Data Specialist',
      utilization: 75,
      activeProjects: 4,
      completedProjects: 15,
      rating: 4.7
    }
  ]
};

const statusColors = {
  'pending': 'bg-yellow-100 text-yellow-800',
  'approved': 'bg-blue-100 text-blue-800',
  'in_progress': 'bg-purple-100 text-purple-800',
  'data_migration': 'bg-orange-100 text-orange-800',
  'system_setup': 'bg-indigo-100 text-indigo-800',
  'training': 'bg-cyan-100 text-cyan-800',
  'testing': 'bg-pink-100 text-pink-800',
  'go_live': 'bg-green-100 text-green-800',
  'completed': 'bg-emerald-100 text-emerald-800',
  'cancelled': 'bg-red-100 text-red-800'
};

const getStatusLabel = (status: string) => {
  const labels = {
    'pending': 'Pending Assignment',
    'approved': 'Approved',
    'in_progress': 'In Progress',
    'data_migration': 'Data Migration',
    'system_setup': 'System Setup',
    'training': 'Training Phase',
    'testing': 'Testing',
    'go_live': 'Go Live',
    'completed': 'Completed',
    'cancelled': 'Cancelled'
  };
  return labels[status] || status;
};

function MetricCard({ title, value, icon, trend, color = 'blue' }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend: string;
  color?: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    emerald: 'bg-emerald-500'
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-sm text-gray-500 mt-1">{trend}</p>
          </div>
          <div className={`p-3 rounded-full ${colorClasses[color]} text-white`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function OrderDetailsModal({ order, isOpen, onClose }: {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!isOpen || !order) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Order Details - {order.id}</CardTitle>
              <CardDescription>{order.schoolName}</CardDescription>
            </div>
            <Button variant="outline" onClick={onClose}>✕</Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Order Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="text-sm text-gray-600">Package</div>
                <div className="font-semibold">{order.package}</div>
                <div className="text-sm text-gray-500">${order.price.toLocaleString()}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="text-sm text-gray-600">Status</div>
                <Badge className={statusColors[order.status]}>
                  {getStatusLabel(order.status)}
                </Badge>
                <div className="mt-2">
                  <Progress value={order.progress} className="h-2" />
                  <div className="text-xs text-gray-500 mt-1">{order.progress}% complete</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="text-sm text-gray-600">Due Date</div>
                <div className="font-semibold">{order.dueDate}</div>
                <div className="text-sm text-gray-500">
                  {Math.ceil((new Date(order.dueDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} days remaining
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Primary Contact</Label>
                <div className="mt-1">
                  <div className="font-medium">{order.contact}</div>
                  <div className="text-sm text-gray-600 flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    {order.email}
                  </div>
                  <div className="text-sm text-gray-600 flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    {order.phone}
                  </div>
                </div>
              </div>
              <div>
                <Label>School Details</Label>
                <div className="mt-1">
                  <div className="font-medium">{order.schoolName}</div>
                  <div className="text-sm text-gray-600">{order.studentCount} students</div>
                  <div className="text-sm text-gray-600">Order Date: {order.orderDate}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Team Assignment */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Team Assignment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label>Migration Manager</Label>
                  <Select defaultValue={order.assignedManager || ''}>
                    <SelectTrigger>
                      <SelectValue placeholder="Assign migration manager" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Sarah Moyo">Sarah Moyo</SelectItem>
                      <SelectItem value="Tendai Chigamba">Tendai Chigamba</SelectItem>
                      <SelectItem value="Grace Mutindi">Grace Mutindi</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Technical Lead</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Assign technical lead" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tech1">John Technical</SelectItem>
                        <SelectItem value="tech2">Mary Developer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Data Specialist</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Assign data specialist" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="data1">Grace Mutindi</SelectItem>
                        <SelectItem value="data2">Peter Data</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Project Notes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Project Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea 
                placeholder="Add project notes, requirements, or special instructions..."
                rows={4}
              />
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2">
            <Button variant="outline">
              <MessageCircle className="h-4 w-4 mr-2" />
              Contact School
            </Button>
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
            <Button>
              <CheckCircle className="h-4 w-4 mr-2" />
              Update Status
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SuperAdminDashboard() {
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showOrderDetails, setShowOrderDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { kpis, orders, team } = mockData;

  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.schoolName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         order.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleOrderClick = (order: Order) => {
    setSelectedOrder(order);
    setShowOrderDetails(true);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Migration Services</h1>
          <p className="text-gray-600">Manage care package orders and migration projects</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create Manual Order
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          title="Active Projects"
          value={kpis.activeProjects}
          icon={<Briefcase className="h-6 w-6" />}
          trend={kpis.trends.projects + " this month"}
          color="blue"
        />
        <MetricCard
          title="Monthly Revenue"
          value={`$${kpis.monthlyRevenue.toLocaleString()}`}
          icon={<DollarSign className="h-6 w-6" />}
          trend={kpis.trends.revenue + " vs last month"}
          color="green"
        />
        <MetricCard
          title="Team Utilization"
          value={`${kpis.teamUtilization}%`}
          icon={<Users className="h-6 w-6" />}
          trend={kpis.trends.utilization}
          color="purple"
        />
        <MetricCard
          title="Success Rate"
          value={`${kpis.successRate}%`}
          icon={<CheckCircle className="h-6 w-6" />}
          trend={kpis.trends.successRate}
          color="emerald"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="orders" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="orders">Care Package Orders</TabsTrigger>
          <TabsTrigger value="projects">Active Projects</TabsTrigger>
          <TabsTrigger value="team">Team Management</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Orders Tab */}
        <TabsContent value="orders" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Care Package Orders</CardTitle>
                  <CardDescription>Manage and track all migration service orders</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Search and Filter */}
              <div className="flex gap-4 mb-6">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search orders by school name or order ID..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="data_migration">Data Migration</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Orders Table */}
              <div className="border rounded-lg">
                <div className="grid grid-cols-12 gap-4 p-4 bg-gray-50 font-medium text-sm border-b">
                  <div className="col-span-2">Order ID</div>
                  <div className="col-span-3">School</div>
                  <div className="col-span-2">Package</div>
                  <div className="col-span-1">Status</div>
                  <div className="col-span-1">Progress</div>
                  <div className="col-span-2">Manager</div>
                  <div className="col-span-1">Actions</div>
                </div>
                
                {filteredOrders.map((order) => (
                  <div key={order.id} className="grid grid-cols-12 gap-4 p-4 border-b hover:bg-gray-50 cursor-pointer"
                       onClick={() => handleOrderClick(order)}>
                    <div className="col-span-2">
                      <div className="font-medium">{order.id}</div>
                      <div className="text-sm text-gray-500">{order.orderDate}</div>
                    </div>
                    <div className="col-span-3">
                      <div className="font-medium">{order.schoolName}</div>
                      <div className="text-sm text-gray-500">{order.studentCount} students</div>
                    </div>
                    <div className="col-span-2">
                      <div className="font-medium">{order.package}</div>
                      <div className="text-sm text-gray-500">${order.price.toLocaleString()}</div>
                    </div>
                    <div className="col-span-1">
                      <Badge className={statusColors[order.status]}>
                        {getStatusLabel(order.status)}
                      </Badge>
                    </div>
                    <div className="col-span-1">
                      <Progress value={order.progress} className="h-2" />
                      <div className="text-xs text-gray-500 mt-1">{order.progress}%</div>
                    </div>
                    <div className="col-span-2">
                      <div className="font-medium">{order.assignedManager || 'Unassigned'}</div>
                      <div className="text-sm text-gray-500">Due: {order.dueDate}</div>
                    </div>
                    <div className="col-span-1">
                      <Button variant="ghost" size="sm" onClick={(e) => {
                        e.stopPropagation();
                        handleOrderClick(order);
                      }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Active Projects Tab */}
        <TabsContent value="projects" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredOrders.filter(order => order.status !== 'completed' && order.status !== 'cancelled').map((project) => (
              <Card key={project.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{project.schoolName}</CardTitle>
                      <CardDescription>{project.id} • {project.package}</CardDescription>
                    </div>
                    <Badge className={statusColors[project.status]}>
                      {getStatusLabel(project.status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Progress</span>
                      <span>{project.progress}%</span>
                    </div>
                    <Progress value={project.progress} className="h-2" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Manager:</span>
                      <div className="font-medium">{project.assignedManager || 'Unassigned'}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Due Date:</span>
                      <div className="font-medium">{project.dueDate}</div>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center pt-2">
                    <div className="text-sm text-gray-500">
                      {project.studentCount} students • ${project.price.toLocaleString()}
                    </div>
                    <Button variant="outline" size="sm" onClick={() => handleOrderClick(project)}>
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Team Management Tab */}
        <TabsContent value="team" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Team Performance</CardTitle>
              <CardDescription>Monitor team utilization and performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {team.map((member) => (
                  <Card key={member.id}>
                    <CardContent className="p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                          {member.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                          <div className="font-semibold">{member.name}</div>
                          <div className="text-sm text-gray-500">{member.role}</div>
                        </div>
                      </div>
                      
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Utilization</span>
                            <span>{member.utilization}%</span>
                          </div>
                          <Progress value={member.utilization} className="h-2" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <span className="text-gray-600">Active:</span>
                            <div className="font-medium">{member.activeProjects}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">Completed:</span>
                            <div className="font-medium">{member.completedProjects}</div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 text-yellow-500" />
                          <span className="font-medium">{member.rating}</span>
                          <span className="text-sm text-gray-500">rating</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Analytics</CardTitle>
                <CardDescription>Monthly revenue breakdown by package type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">Foundation Package</div>
                      <div className="text-sm text-gray-500">8 orders this month</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">$22,400</div>
                      <div className="text-sm text-gray-500">14% of total</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">Growth Package</div>
                      <div className="text-sm text-gray-500">12 orders this month</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">$78,000</div>
                      <div className="text-sm text-gray-500">50% of total</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">Enterprise Package</div>
                      <div className="text-sm text-gray-500">4 orders this month</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">$60,000</div>
                      <div className="text-sm text-gray-500">38% of total</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Average Completion Time</span>
                    <span className="font-semibold">18 days</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Customer Satisfaction</span>
                    <span className="font-semibold">4.8/5.0</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">On-Time Delivery</span>
                    <span className="font-semibold">94%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Referral Rate</span>
                    <span className="font-semibold">42%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Upsell Rate</span>
                    <span className="font-semibold">28%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Trends</CardTitle>
              <CardDescription>Revenue and project volume over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                <div className="text-center text-gray-500">
                  <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                  <div>Revenue and project trend chart would be displayed here</div>
                  <div className="text-sm">Integration with charting library needed</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Order Details Modal */}
      <OrderDetailsModal 
        order={selectedOrder}
        isOpen={showOrderDetails}
        onClose={() => setShowOrderDetails(false)}
      />
    </div>
  );
}