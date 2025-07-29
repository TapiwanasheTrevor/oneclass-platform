/**
 * User Management Component
 * Main component for managing users within schools with role-based access
 */

import React, { useState, useEffect } from 'react';
import { Plus, Users, UserPlus, Upload, Filter, Search, MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';

import { useAuth, usePermissions, useSchoolContext } from '@/hooks/useAuth';
import { UserCreateForm } from './UserCreateForm';
import { UserInviteForm } from './UserInviteForm';
import { BulkImportDialog } from './BulkImportDialog';
import { UserProfileDialog } from './UserProfileDialog';
import { InvitationsList } from './InvitationsList';
import { SchoolMembershipManager } from './SchoolMembershipManager';

interface PlatformUserData {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  platform_role: string;
  status: string;
  primary_school_id?: string;
  school_memberships: {
    school_id: string;
    school_name: string;
    school_subdomain: string;
    role: string;
    permissions: string[];
    joined_date: string;
    status: string;
    student_id?: string;
    current_grade?: string;
    employee_id?: string;
    department?: string;
    children_ids?: string[];
  }[];
  profile?: {
    phone_number?: string;
    profile_image_url?: string;
    date_of_birth?: string;
    gender?: string;
    address?: string;
    department?: string;
    position?: string;
    employee_id?: string;
    student_id?: string;
    grade_level?: string;
  };
  created_at: string;
  last_login?: string;
  feature_flags: Record<string, boolean>;
  user_preferences: Record<string, any>;
}

interface UserFilters {
  query: string;
  platform_role: string;
  school_role: string;
  department: string;
  status: string;
  school_id: string;
}

const platformRoleColors = {
  super_admin: 'bg-purple-100 text-purple-800',
  school_admin: 'bg-red-100 text-red-800',
  registrar: 'bg-blue-100 text-blue-800',
  teacher: 'bg-green-100 text-green-800',
  staff: 'bg-gray-100 text-gray-800',
  parent: 'bg-yellow-100 text-yellow-800',
  student: 'bg-orange-100 text-orange-800',
};

const schoolRoleColors = {
  principal: 'bg-purple-100 text-purple-800',
  deputy_principal: 'bg-indigo-100 text-indigo-800',
  academic_head: 'bg-blue-100 text-blue-800',
  department_head: 'bg-cyan-100 text-cyan-800',
  teacher: 'bg-green-100 text-green-800',
  form_teacher: 'bg-emerald-100 text-emerald-800',
  registrar: 'bg-blue-100 text-blue-800',
  bursar: 'bg-amber-100 text-amber-800',
  librarian: 'bg-teal-100 text-teal-800',
  it_support: 'bg-slate-100 text-slate-800',
  security: 'bg-stone-100 text-stone-800',
  parent: 'bg-yellow-100 text-yellow-800',
  student: 'bg-orange-100 text-orange-800',
};

const platformRoleLabels = {
  super_admin: 'Super Admin',
  school_admin: 'School Admin',
  registrar: 'Registrar',
  teacher: 'Teacher',
  staff: 'Staff',
  parent: 'Parent',
  student: 'Student',
};

const schoolRoleLabels = {
  principal: 'Principal',
  deputy_principal: 'Deputy Principal',
  academic_head: 'Academic Head',
  department_head: 'Department Head',
  teacher: 'Teacher',
  form_teacher: 'Form Teacher',
  registrar: 'Registrar',
  bursar: 'Bursar',
  librarian: 'Librarian',
  it_support: 'IT Support',
  security: 'Security',
  parent: 'Parent',
  student: 'Student',
};

const statusColors = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  suspended: 'bg-red-100 text-red-800',
  pending_verification: 'bg-yellow-100 text-yellow-800',
  archived: 'bg-slate-100 text-slate-800',
};

const statusLabels = {
  active: 'Active',
  inactive: 'Inactive',
  suspended: 'Suspended',
  pending_verification: 'Pending Verification',
  archived: 'Archived',
};

export const UserManagement: React.FC = () => {
  const { user, token } = useAuth();
  const { currentSchool, availableSchools, switchSchool } = useSchoolContext();
  const { canManageUsers, canViewReports, hasPermission } = usePermissions();
  
  const [users, setUsers] = useState<PlatformUserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<PlatformUserData | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showMembershipManager, setShowMembershipManager] = useState(false);
  const [activeTab, setActiveTab] = useState('users');
  
  const [filters, setFilters] = useState<UserFilters>({
    query: '',
    platform_role: '',
    school_role: '',
    department: '',
    status: '',
    school_id: currentSchool?.school_id || '',
  });
  
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  });

  // Check permissions
  const canCreateUsers = hasPermission('users.create');
  const canUpdateUsers = hasPermission('users.update');
  const canDeleteUsers = hasPermission('users.delete');
  const canInviteUsers = hasPermission('users.invite');
  const canBulkImport = hasPermission('users.bulk_import');
  const canManageSchools = hasPermission('schools.manage');

  // Fetch users
  const fetchUsers = async () => {
    try {
      setLoading(true);
      
      const queryParams = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
        ...(filters.query && { query: filters.query }),
        ...(filters.platform_role && { platform_role: filters.platform_role }),
        ...(filters.school_role && { school_role: filters.school_role }),
        ...(filters.department && { department: filters.department }),
        ...(filters.status && { status: filters.status }),
        ...(filters.school_id && { school_id: filters.school_id }),
      });
      
      const response = await fetch(`/api/v1/users?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }
      
      const data = await response.json();
      setUsers(data.users);
      setPagination({
        page: data.page,
        page_size: data.page_size,
        total: data.total,
        total_pages: data.total_pages,
      });
    } catch (error) {
      toast.error('Failed to fetch users');
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [filters, pagination.page, pagination.page_size]);

  // Handle user creation
  const handleUserCreated = (newUser: PlatformUserData) => {
    setUsers(prev => [newUser, ...prev]);
    setShowCreateForm(false);
    toast.success('User created successfully');
    fetchUsers(); // Refresh to get updated data
  };

  // Handle user invitation
  const handleUserInvited = () => {
    setShowInviteForm(false);
    toast.success('User invitation sent successfully');
  };

  // Handle bulk import
  const handleBulkImportComplete = () => {
    setShowBulkImport(false);
    fetchUsers(); // Refresh the user list
    toast.success('Bulk import completed');
  };

  // Handle user update
  const handleUserUpdate = async (userId: string, updates: Partial<PlatformUserData>) => {
    try {
      const response = await fetch(`/api/v1/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Failed to update user');
      }

      const updatedUser = await response.json();
      setUsers(prev => 
        prev.map(u => u.id === userId ? { ...u, ...updatedUser } : u)
      );
      
      toast.success('User updated successfully');
    } catch (error) {
      toast.error('Failed to update user');
      console.error('Error updating user:', error);
    }
  };

  // Handle user deletion
  const handleUserDelete = async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete user');
      }

      setUsers(prev => prev.filter(u => u.id !== userId));
      toast.success('User deleted successfully');
    } catch (error) {
      toast.error('Failed to delete user');
      console.error('Error deleting user:', error);
    }
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof UserFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? '' : value,
    }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  // Effect to update school filter when current school changes
  useEffect(() => {
    if (currentSchool && filters.school_id !== currentSchool.school_id) {
      setFilters(prev => ({ ...prev, school_id: currentSchool.school_id }));
    }
  }, [currentSchool]);

  // Reset filters
  const resetFilters = () => {
    setFilters({
      query: '',
      platform_role: '',
      school_role: '',
      department: '',
      status: '',
      school_id: currentSchool?.school_id || '',
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  // Handle school switch
  const handleSchoolSwitch = (schoolId: string) => {
    switchSchool(schoolId);
    setFilters(prev => ({ ...prev, school_id: schoolId }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">User Management</h1>
          <p className="text-gray-600">Manage users and their roles within your schools</p>
          {currentSchool && (
            <p className="text-sm text-blue-600">Current school: {currentSchool.school_name}</p>
          )}
        </div>
        
        <div className="flex gap-2">
          {canBulkImport && (
            <Button
              variant="outline"
              onClick={() => setShowBulkImport(true)}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Bulk Import
            </Button>
          )}
          
          {canInviteUsers && (
            <Button
              variant="outline"
              onClick={() => setShowInviteForm(true)}
              className="flex items-center gap-2"
            >
              <UserPlus className="h-4 w-4" />
              Invite User
            </Button>
          )}
          
          {canCreateUsers && (
            <Button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Create User
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="invitations" className="flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            Invitations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-6">
          {/* School Selector & Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Filters & School Selection
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* School Selector */}
                {canManageSchools && availableSchools.length > 1 && (
                  <div>
                    <label className="block text-sm font-medium mb-2">School</label>
                    <Select value={filters.school_id} onValueChange={(value) => handleSchoolSwitch(value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select school" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableSchools.map((school) => (
                          <SelectItem key={school.school_id} value={school.school_id}>
                            {school.school_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-2">Search</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search users..."
                      value={filters.query}
                      onChange={(e) => handleFilterChange('query', e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Platform Role</label>
                  <Select value={filters.platform_role} onValueChange={(value) => handleFilterChange('platform_role', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="All platform roles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All platform roles</SelectItem>
                      <SelectItem value="super_admin">Super Admin</SelectItem>
                      <SelectItem value="school_admin">School Admin</SelectItem>
                      <SelectItem value="registrar">Registrar</SelectItem>
                      <SelectItem value="teacher">Teacher</SelectItem>
                      <SelectItem value="staff">Staff</SelectItem>
                      <SelectItem value="parent">Parent</SelectItem>
                      <SelectItem value="student">Student</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">School Role</label>
                  <Select value={filters.school_role} onValueChange={(value) => handleFilterChange('school_role', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="All school roles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All school roles</SelectItem>
                      <SelectItem value="principal">Principal</SelectItem>
                      <SelectItem value="deputy_principal">Deputy Principal</SelectItem>
                      <SelectItem value="academic_head">Academic Head</SelectItem>
                      <SelectItem value="department_head">Department Head</SelectItem>
                      <SelectItem value="teacher">Teacher</SelectItem>
                      <SelectItem value="form_teacher">Form Teacher</SelectItem>
                      <SelectItem value="registrar">Registrar</SelectItem>
                      <SelectItem value="bursar">Bursar</SelectItem>
                      <SelectItem value="librarian">Librarian</SelectItem>
                      <SelectItem value="it_support">IT Support</SelectItem>
                      <SelectItem value="security">Security</SelectItem>
                      <SelectItem value="parent">Parent</SelectItem>
                      <SelectItem value="student">Student</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Status</label>
                  <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="All statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All statuses</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="suspended">Suspended</SelectItem>
                      <SelectItem value="pending_verification">Pending Verification</SelectItem>
                      <SelectItem value="archived">Archived</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex items-end">
                  <Button variant="outline" onClick={resetFilters}>
                    Clear Filters
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Users Table */}
          <Card>
            <CardHeader>
              <CardTitle>Users ({pagination.total})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Platform Role</TableHead>
                    <TableHead>School Role</TableHead>
                    <TableHead>School</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        Loading users...
                      </TableCell>
                    </TableRow>
                  ) : users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        No users found
                      </TableCell>
                    </TableRow>
                  ) : (
                    users.map((user) => {
                      const currentSchoolMembership = user.school_memberships.find(
                        m => m.school_id === (filters.school_id || currentSchool?.school_id)
                      ) || user.school_memberships[0];
                      
                      return (
                        <TableRow key={user.id}>
                          <TableCell>
                            <div className="font-medium">
                              {user.full_name}
                            </div>
                            {currentSchoolMembership?.employee_id && (
                              <div className="text-sm text-gray-500">
                                Employee ID: {currentSchoolMembership.employee_id}
                              </div>
                            )}
                            {currentSchoolMembership?.student_id && (
                              <div className="text-sm text-gray-500">
                                Student ID: {currentSchoolMembership.student_id}
                              </div>
                            )}
                            {currentSchoolMembership?.current_grade && (
                              <div className="text-sm text-gray-500">
                                Grade: {currentSchoolMembership.current_grade}
                              </div>
                            )}
                          </TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            <Badge className={platformRoleColors[user.platform_role as keyof typeof platformRoleColors]}>
                              {platformRoleLabels[user.platform_role as keyof typeof platformRoleLabels]}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {currentSchoolMembership ? (
                              <Badge className={schoolRoleColors[currentSchoolMembership.role as keyof typeof schoolRoleColors]}>
                                {schoolRoleLabels[currentSchoolMembership.role as keyof typeof schoolRoleLabels]}
                              </Badge>
                            ) : (
                              <span className="text-gray-400">No school role</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {currentSchoolMembership ? (
                              <div>
                                <div className="font-medium">{currentSchoolMembership.school_name}</div>
                                <div className="text-sm text-gray-500">
                                  {currentSchoolMembership.department || 'No department'}
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400">No school</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge className={statusColors[user.status as keyof typeof statusColors]}>
                              {statusLabels[user.status as keyof typeof statusLabels]}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {user.last_login ? (
                              new Date(user.last_login).toLocaleDateString()
                            ) : (
                              <span className="text-gray-400">Never</span>
                            )}
                          </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setShowProfile(true);
                                }}
                              >
                                View Profile
                              </DropdownMenuItem>
                              {canUpdateUsers && (
                                <DropdownMenuItem
                                  onClick={() => handleUserUpdate(user.id, { 
                                    status: user.status === 'active' ? 'inactive' : 'active' 
                                  })}
                                >
                                  {user.status === 'active' ? 'Deactivate' : 'Activate'}
                                </DropdownMenuItem>
                              )}
                              {canUpdateUsers && user.status === 'active' && (
                                <DropdownMenuItem
                                  onClick={() => handleUserUpdate(user.id, { status: 'suspended' })}
                                  className="text-orange-600"
                                >
                                  Suspend
                                </DropdownMenuItem>
                              )}
                              {canUpdateUsers && (
                                <DropdownMenuItem
                                  onClick={() => {
                                    setSelectedUser(user);
                                    setShowMembershipManager(true);
                                  }}
                                >
                                  Manage School Memberships
                                </DropdownMenuItem>
                              )}
                              {canDeleteUsers && (
                                <DropdownMenuItem
                                  onClick={() => handleUserDelete(user.id)}
                                  className="text-red-600"
                                >
                                  Delete
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              {pagination.total_pages > 1 && (
                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-gray-600">
                    Showing {((pagination.page - 1) * pagination.page_size) + 1} to{' '}
                    {Math.min(pagination.page * pagination.page_size, pagination.total)} of{' '}
                    {pagination.total} users
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.page === pagination.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invitations">
          <InvitationsList />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <Dialog open={showCreateForm} onOpenChange={setShowCreateForm}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
          </DialogHeader>
          <UserCreateForm
            onUserCreated={handleUserCreated}
            onCancel={() => setShowCreateForm(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={showInviteForm} onOpenChange={setShowInviteForm}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Invite User</DialogTitle>
          </DialogHeader>
          <UserInviteForm
            onUserInvited={handleUserInvited}
            onCancel={() => setShowInviteForm(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={showBulkImport} onOpenChange={setShowBulkImport}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Bulk Import Users</DialogTitle>
          </DialogHeader>
          <BulkImportDialog
            onImportComplete={handleBulkImportComplete}
            onCancel={() => setShowBulkImport(false)}
          />
        </DialogContent>
      </Dialog>

      {selectedUser && (
        <>
          <Dialog open={showProfile} onOpenChange={setShowProfile}>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>User Profile</DialogTitle>
              </DialogHeader>
              <UserProfileDialog
                user={selectedUser}
                onUpdate={(updates) => handleUserUpdate(selectedUser.id, updates)}
                onClose={() => setShowProfile(false)}
              />
            </DialogContent>
          </Dialog>

          <Dialog open={showMembershipManager} onOpenChange={setShowMembershipManager}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage School Memberships</DialogTitle>
              </DialogHeader>
              <SchoolMembershipManager
                user={selectedUser as any} // Type conversion for compatibility
                onMembershipUpdate={(updatedUser) => {
                  setUsers(prev => 
                    prev.map(u => u.id === updatedUser.id ? { ...u, ...updatedUser } : u)
                  );
                  setSelectedUser(updatedUser as any);
                }}
              />
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
};