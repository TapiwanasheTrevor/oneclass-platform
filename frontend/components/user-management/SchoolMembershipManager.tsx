/**
 * School Membership Management Component
 * Allows managing user memberships across multiple schools
 */

import React, { useState, useEffect } from 'react';
import { Plus, X, Edit, Trash2, Users, School } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

import { useAuth, usePermissions, PlatformUser, SchoolRole, UserStatus } from '@/hooks/useAuth';

interface SchoolMembership {
  school_id: string;
  school_name: string;
  school_subdomain: string;
  role: SchoolRole;
  permissions: string[];
  joined_date: string;
  status: UserStatus;
  
  // Role-specific fields
  student_id?: string;
  current_grade?: string;
  admission_date?: string;
  graduation_date?: string;
  
  employee_id?: string;
  department?: string;
  hire_date?: string;
  contract_type?: string;
  
  children_ids?: string[];
}

interface School {
  id: string;
  name: string;
  subdomain: string;
  address: string;
  phone: string;
  email: string;
}

interface SchoolMembershipManagerProps {
  user: PlatformUser;
  onMembershipUpdate: (updatedUser: PlatformUser) => void;
}

export const SchoolMembershipManager: React.FC<SchoolMembershipManagerProps> = ({
  user,
  onMembershipUpdate
}) => {
  const { token } = useAuth();
  const { canManageUsers, isPlatformAdmin } = usePermissions();
  
  const [memberships, setMemberships] = useState<SchoolMembership[]>(user.school_memberships);
  const [availableSchools, setAvailableSchools] = useState<School[]>([]);
  const [showAddMembership, setShowAddMembership] = useState(false);
  const [editingMembership, setEditingMembership] = useState<SchoolMembership | null>(null);
  const [loading, setLoading] = useState(false);
  
  // New membership form state
  const [newMembership, setNewMembership] = useState<Partial<SchoolMembership>>({
    role: SchoolRole.STUDENT,
    status: UserStatus.ACTIVE,
    permissions: [],
  });

  // Fetch available schools
  useEffect(() => {
    fetchAvailableSchools();
  }, []);

  const fetchAvailableSchools = async () => {
    try {
      const response = await fetch('/api/v1/schools', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const schools = await response.json();
        setAvailableSchools(schools);
      }
    } catch (error) {
      console.error('Error fetching schools:', error);
    }
  };

  const getAvailableSchoolsForUser = () => {
    const userSchoolIds = memberships.map(m => m.school_id);
    return availableSchools.filter(school => !userSchoolIds.includes(school.id));
  };

  const getDefaultPermissionsForRole = (role: SchoolRole): string[] => {
    const rolePermissions: Record<SchoolRole, string[]> = {
      [SchoolRole.PRINCIPAL]: ['*'],
      [SchoolRole.DEPUTY_PRINCIPAL]: ['users.manage', 'academics.manage', 'reports.view'],
      [SchoolRole.ACADEMIC_HEAD]: ['academics.manage', 'reports.view', 'students.manage'],
      [SchoolRole.DEPARTMENT_HEAD]: ['academics.view', 'students.manage', 'reports.view'],
      [SchoolRole.TEACHER]: ['students.view', 'academics.view', 'attendance.manage'],
      [SchoolRole.FORM_TEACHER]: ['students.manage', 'academics.view', 'attendance.manage'],
      [SchoolRole.REGISTRAR]: ['students.manage', 'documents.manage', 'reports.view'],
      [SchoolRole.BURSAR]: ['finance.manage', 'payments.process', 'reports.financial'],
      [SchoolRole.LIBRARIAN]: ['library.manage', 'resources.manage'],
      [SchoolRole.IT_SUPPORT]: ['system.support', 'users.support'],
      [SchoolRole.SECURITY]: ['security.manage', 'access.control'],
      [SchoolRole.PARENT]: ['students.view', 'payments.view', 'communication.receive'],
      [SchoolRole.STUDENT]: ['academics.view', 'assignments.submit', 'resources.access'],
    };
    
    return rolePermissions[role] || [];
  };

  const handleAddMembership = async () => {
    if (!newMembership.school_id || !newMembership.role) {
      toast.error('Please select a school and role');
      return;
    }

    setLoading(true);
    try {
      const school = availableSchools.find(s => s.id === newMembership.school_id);
      if (!school) {
        throw new Error('School not found');
      }

      const membershipData = {
        ...newMembership,
        school_name: school.name,
        school_subdomain: school.subdomain,
        joined_date: new Date().toISOString(),
        permissions: newMembership.permissions?.length ? newMembership.permissions : getDefaultPermissionsForRole(newMembership.role as SchoolRole),
      };

      const response = await fetch(`/api/v1/users/${user.id}/school-memberships`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(membershipData),
      });

      if (!response.ok) {
        throw new Error('Failed to add membership');
      }

      const updatedUser = await response.json();
      setMemberships(updatedUser.school_memberships);
      onMembershipUpdate(updatedUser);
      
      setShowAddMembership(false);
      setNewMembership({
        role: SchoolRole.STUDENT,
        status: UserStatus.ACTIVE,
        permissions: [],
      });
      
      toast.success('School membership added successfully');
    } catch (error) {
      toast.error('Failed to add school membership');
      console.error('Error adding membership:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMembership = async (membership: SchoolMembership) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/users/${user.id}/school-memberships/${membership.school_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(membership),
      });

      if (!response.ok) {
        throw new Error('Failed to update membership');
      }

      const updatedUser = await response.json();
      setMemberships(updatedUser.school_memberships);
      onMembershipUpdate(updatedUser);
      setEditingMembership(null);
      
      toast.success('School membership updated successfully');
    } catch (error) {
      toast.error('Failed to update school membership');
      console.error('Error updating membership:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMembership = async (schoolId: string) => {
    if (!confirm('Are you sure you want to remove this school membership?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/users/${user.id}/school-memberships/${schoolId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to remove membership');
      }

      const updatedUser = await response.json();
      setMemberships(updatedUser.school_memberships);
      onMembershipUpdate(updatedUser);
      
      toast.success('School membership removed successfully');
    } catch (error) {
      toast.error('Failed to remove school membership');
      console.error('Error removing membership:', error);
    } finally {
      setLoading(false);
    }
  };

  const canEditMembership = (membership: SchoolMembership): boolean => {
    return isPlatformAdmin || canManageUsers(membership.school_id);
  };

  const getRoleColor = (role: SchoolRole): string => {
    const colors: Record<SchoolRole, string> = {
      [SchoolRole.PRINCIPAL]: 'bg-purple-100 text-purple-800',
      [SchoolRole.DEPUTY_PRINCIPAL]: 'bg-indigo-100 text-indigo-800',
      [SchoolRole.ACADEMIC_HEAD]: 'bg-blue-100 text-blue-800',
      [SchoolRole.DEPARTMENT_HEAD]: 'bg-cyan-100 text-cyan-800',
      [SchoolRole.TEACHER]: 'bg-green-100 text-green-800',
      [SchoolRole.FORM_TEACHER]: 'bg-emerald-100 text-emerald-800',
      [SchoolRole.REGISTRAR]: 'bg-blue-100 text-blue-800',
      [SchoolRole.BURSAR]: 'bg-amber-100 text-amber-800',
      [SchoolRole.LIBRARIAN]: 'bg-teal-100 text-teal-800',
      [SchoolRole.IT_SUPPORT]: 'bg-slate-100 text-slate-800',
      [SchoolRole.SECURITY]: 'bg-stone-100 text-stone-800',
      [SchoolRole.PARENT]: 'bg-yellow-100 text-yellow-800',
      [SchoolRole.STUDENT]: 'bg-orange-100 text-orange-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: UserStatus): string => {
    const colors: Record<UserStatus, string> = {
      [UserStatus.ACTIVE]: 'bg-green-100 text-green-800',
      [UserStatus.INACTIVE]: 'bg-gray-100 text-gray-800',
      [UserStatus.SUSPENDED]: 'bg-red-100 text-red-800',
      [UserStatus.PENDING_VERIFICATION]: 'bg-yellow-100 text-yellow-800',
      [UserStatus.ARCHIVED]: 'bg-slate-100 text-slate-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <School className="h-5 w-5" />
            School Memberships
          </h3>
          <p className="text-sm text-gray-600">
            Manage {user.full_name}'s memberships across different schools
          </p>
        </div>
        
        {(isPlatformAdmin || canManageUsers()) && getAvailableSchoolsForUser().length > 0 && (
          <Dialog open={showAddMembership} onOpenChange={setShowAddMembership}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Add School Membership
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add School Membership</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="school">School</Label>
                  <Select 
                    value={newMembership.school_id || ''} 
                    onValueChange={(value) => setNewMembership(prev => ({ ...prev, school_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a school" />
                    </SelectTrigger>
                    <SelectContent>
                      {getAvailableSchoolsForUser().map((school) => (
                        <SelectItem key={school.id} value={school.id}>
                          {school.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Select 
                    value={newMembership.role || ''} 
                    onValueChange={(value) => {
                      const role = value as SchoolRole;
                      setNewMembership(prev => ({ 
                        ...prev, 
                        role,
                        permissions: getDefaultPermissionsForRole(role)
                      }));
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a role" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.values(SchoolRole).map((role) => (
                        <SelectItem key={role} value={role}>
                          {role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {newMembership.role === SchoolRole.STUDENT && (
                  <>
                    <div>
                      <Label htmlFor="student_id">Student ID</Label>
                      <Input
                        id="student_id"
                        value={newMembership.student_id || ''}
                        onChange={(e) => setNewMembership(prev => ({ ...prev, student_id: e.target.value }))}
                        placeholder="Enter student ID"
                      />
                    </div>
                    <div>
                      <Label htmlFor="current_grade">Current Grade</Label>
                      <Input
                        id="current_grade"
                        value={newMembership.current_grade || ''}
                        onChange={(e) => setNewMembership(prev => ({ ...prev, current_grade: e.target.value }))}
                        placeholder="Enter current grade"
                      />
                    </div>
                  </>
                )}
                
                {newMembership.role && ![SchoolRole.STUDENT, SchoolRole.PARENT].includes(newMembership.role as SchoolRole) && (
                  <>
                    <div>
                      <Label htmlFor="employee_id">Employee ID</Label>
                      <Input
                        id="employee_id"
                        value={newMembership.employee_id || ''}
                        onChange={(e) => setNewMembership(prev => ({ ...prev, employee_id: e.target.value }))}
                        placeholder="Enter employee ID"
                      />
                    </div>
                    <div>
                      <Label htmlFor="department">Department</Label>
                      <Input
                        id="department"
                        value={newMembership.department || ''}
                        onChange={(e) => setNewMembership(prev => ({ ...prev, department: e.target.value }))}
                        placeholder="Enter department"
                      />
                    </div>
                  </>
                )}
                
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowAddMembership(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddMembership} disabled={loading}>
                    {loading ? 'Adding...' : 'Add Membership'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Memberships List */}
      <div className="grid gap-4">
        {memberships.map((membership) => (
          <Card key={membership.school_id}>
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h4 className="font-semibold text-lg">{membership.school_name}</h4>
                    <Badge className={getRoleColor(membership.role)}>
                      {membership.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                    <Badge className={getStatusColor(membership.status)}>
                      {membership.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-500">Joined Date:</span>
                      <p>{new Date(membership.joined_date).toLocaleDateString()}</p>
                    </div>
                    
                    {membership.student_id && (
                      <div>
                        <span className="font-medium text-gray-500">Student ID:</span>
                        <p>{membership.student_id}</p>
                      </div>
                    )}
                    
                    {membership.current_grade && (
                      <div>
                        <span className="font-medium text-gray-500">Grade:</span>
                        <p>{membership.current_grade}</p>
                      </div>
                    )}
                    
                    {membership.employee_id && (
                      <div>
                        <span className="font-medium text-gray-500">Employee ID:</span>
                        <p>{membership.employee_id}</p>
                      </div>
                    )}
                    
                    {membership.department && (
                      <div>
                        <span className="font-medium text-gray-500">Department:</span>
                        <p>{membership.department}</p>
                      </div>
                    )}
                    
                    <div>
                      <span className="font-medium text-gray-500">Permissions:</span>
                      <p>{membership.permissions.length} permission(s)</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {canEditMembership(membership) && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingMembership(membership)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRemoveMembership(membership.school_id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {memberships.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center">
              <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h4 className="text-lg font-medium text-gray-600 mb-2">No School Memberships</h4>
              <p className="text-gray-500">This user is not currently a member of any schools.</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Membership Dialog */}
      {editingMembership && (
        <Dialog open={!!editingMembership} onOpenChange={() => setEditingMembership(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit School Membership - {editingMembership.school_name}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit_role">Role</Label>
                <Select 
                  value={editingMembership.role} 
                  onValueChange={(value) => setEditingMembership(prev => prev ? { 
                    ...prev, 
                    role: value as SchoolRole,
                    permissions: getDefaultPermissionsForRole(value as SchoolRole)
                  } : null)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(SchoolRole).map((role) => (
                      <SelectItem key={role} value={role}>
                        {role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="edit_status">Status</Label>
                <Select 
                  value={editingMembership.status} 
                  onValueChange={(value) => setEditingMembership(prev => prev ? { 
                    ...prev, 
                    status: value as UserStatus 
                  } : null)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(UserStatus).map((status) => (
                      <SelectItem key={status} value={status}>
                        {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {editingMembership.role === SchoolRole.STUDENT && (
                <>
                  <div>
                    <Label htmlFor="edit_student_id">Student ID</Label>
                    <Input
                      id="edit_student_id"
                      value={editingMembership.student_id || ''}
                      onChange={(e) => setEditingMembership(prev => prev ? { 
                        ...prev, 
                        student_id: e.target.value 
                      } : null)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit_current_grade">Current Grade</Label>
                    <Input
                      id="edit_current_grade"
                      value={editingMembership.current_grade || ''}
                      onChange={(e) => setEditingMembership(prev => prev ? { 
                        ...prev, 
                        current_grade: e.target.value 
                      } : null)}
                    />
                  </div>
                </>
              )}
              
              {editingMembership.role && ![SchoolRole.STUDENT, SchoolRole.PARENT].includes(editingMembership.role) && (
                <>
                  <div>
                    <Label htmlFor="edit_employee_id">Employee ID</Label>
                    <Input
                      id="edit_employee_id"
                      value={editingMembership.employee_id || ''}
                      onChange={(e) => setEditingMembership(prev => prev ? { 
                        ...prev, 
                        employee_id: e.target.value 
                      } : null)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit_department">Department</Label>
                    <Input
                      id="edit_department"
                      value={editingMembership.department || ''}
                      onChange={(e) => setEditingMembership(prev => prev ? { 
                        ...prev, 
                        department: e.target.value 
                      } : null)}
                    />
                  </div>
                </>
              )}
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingMembership(null)}>
                  Cancel
                </Button>
                <Button 
                  onClick={() => editingMembership && handleUpdateMembership(editingMembership)} 
                  disabled={loading}
                >
                  {loading ? 'Updating...' : 'Update Membership'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};