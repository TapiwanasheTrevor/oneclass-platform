/**
 * User Create Form Component
 * Form for creating new users with role-specific fields
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

import { useAuth } from '@/hooks/useAuth';
import { useSchoolContext } from '@/hooks/useSchoolContext';

interface UserCreateFormProps {
  onUserCreated: (user: any) => void;
  onCancel: () => void;
}

interface UserFormData {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: string;
  password: string;
  send_invitation: boolean;
  
  // Role-specific fields
  department: string;
  position: string;
  employee_id: string;
  student_id: string;
  grade_level: string;
  
  // Additional metadata
  role_metadata: Record<string, any>;
  permissions: string[];
}

const defaultFormData: UserFormData = {
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  role: 'student',
  password: '',
  send_invitation: true,
  department: '',
  position: '',
  employee_id: '',
  student_id: '',
  grade_level: '',
  role_metadata: {},
  permissions: [],
};

const roleRequiredFields = {
  school_admin: ['department', 'position'],
  registrar: ['department', 'position'],
  teacher: ['department', 'position'],
  staff: ['department', 'position'],
  student: ['grade_level'],
  parent: [],
};

const gradeLevels = [
  'Pre-K', 'K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'
];

const departments = [
  'Administration',
  'Mathematics',
  'Science',
  'English',
  'History',
  'Physical Education',
  'Art',
  'Music',
  'Technology',
  'Counseling',
  'Library',
  'Special Education',
  'Other'
];

export const UserCreateForm: React.FC<UserCreateFormProps> = ({
  onUserCreated,
  onCancel
}) => {
  const { user } = useAuth();
  const { canAccess } = useSchoolContext();
  
  const [formData, setFormData] = useState<UserFormData>(defaultFormData);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Handle form field changes
  const handleFieldChange = (field: keyof UserFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Required fields validation
    if (!formData.email) newErrors.email = 'Email is required';
    if (!formData.first_name) newErrors.first_name = 'First name is required';
    if (!formData.last_name) newErrors.last_name = 'Last name is required';
    if (!formData.role) newErrors.role = 'Role is required';
    
    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    // Password validation (if not sending invitation)
    if (!formData.send_invitation && !formData.password) {
      newErrors.password = 'Password is required when not sending invitation';
    }
    
    if (formData.password && formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    // Role-specific field validation
    const requiredFields = roleRequiredFields[formData.role as keyof typeof roleRequiredFields] || [];
    requiredFields.forEach(field => {
      if (!formData[field as keyof UserFormData]) {
        newErrors[field] = `${field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} is required for this role`;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }
      
      const newUser = await response.json();
      onUserCreated(newUser);
      
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create user');
      console.error('Error creating user:', error);
    } finally {
      setLoading(false);
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData(defaultFormData);
    setErrors({});
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="first_name">First Name *</Label>
            <Input
              id="first_name"
              value={formData.first_name}
              onChange={(e) => handleFieldChange('first_name', e.target.value)}
              className={errors.first_name ? 'border-red-500' : ''}
            />
            {errors.first_name && (
              <p className="text-sm text-red-500 mt-1">{errors.first_name}</p>
            )}
          </div>
          
          <div>
            <Label htmlFor="last_name">Last Name *</Label>
            <Input
              id="last_name"
              value={formData.last_name}
              onChange={(e) => handleFieldChange('last_name', e.target.value)}
              className={errors.last_name ? 'border-red-500' : ''}
            />
            {errors.last_name && (
              <p className="text-sm text-red-500 mt-1">{errors.last_name}</p>
            )}
          </div>
          
          <div>
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleFieldChange('email', e.target.value)}
              className={errors.email ? 'border-red-500' : ''}
            />
            {errors.email && (
              <p className="text-sm text-red-500 mt-1">{errors.email}</p>
            )}
          </div>
          
          <div>
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              type="tel"
              value={formData.phone}
              onChange={(e) => handleFieldChange('phone', e.target.value)}
            />
          </div>
          
          <div>
            <Label htmlFor="role">Role *</Label>
            <Select value={formData.role} onValueChange={(value) => handleFieldChange('role', value)}>
              <SelectTrigger className={errors.role ? 'border-red-500' : ''}>
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                {canAccess('users.create.admin') && (
                  <SelectItem value="school_admin">School Admin</SelectItem>
                )}
                {canAccess('users.create.staff') && (
                  <>
                    <SelectItem value="registrar">Registrar</SelectItem>
                    <SelectItem value="teacher">Teacher</SelectItem>
                    <SelectItem value="staff">Staff</SelectItem>
                  </>
                )}
                {canAccess('users.create.student') && (
                  <SelectItem value="student">Student</SelectItem>
                )}
                {canAccess('users.create.parent') && (
                  <SelectItem value="parent">Parent</SelectItem>
                )}
              </SelectContent>
            </Select>
            {errors.role && (
              <p className="text-sm text-red-500 mt-1">{errors.role}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Role-specific Information */}
      <Card>
        <CardHeader>
          <CardTitle>Role-specific Information</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Staff/Teacher/Admin fields */}
          {['school_admin', 'registrar', 'teacher', 'staff'].includes(formData.role) && (
            <>
              <div>
                <Label htmlFor="department">Department *</Label>
                <Select value={formData.department} onValueChange={(value) => handleFieldChange('department', value)}>
                  <SelectTrigger className={errors.department ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map(dept => (
                      <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.department && (
                  <p className="text-sm text-red-500 mt-1">{errors.department}</p>
                )}
              </div>
              
              <div>
                <Label htmlFor="position">Position *</Label>
                <Input
                  id="position"
                  value={formData.position}
                  onChange={(e) => handleFieldChange('position', e.target.value)}
                  className={errors.position ? 'border-red-500' : ''}
                  placeholder="e.g., Mathematics Teacher, Vice Principal"
                />
                {errors.position && (
                  <p className="text-sm text-red-500 mt-1">{errors.position}</p>
                )}
              </div>
              
              <div>
                <Label htmlFor="employee_id">Employee ID</Label>
                <Input
                  id="employee_id"
                  value={formData.employee_id}
                  onChange={(e) => handleFieldChange('employee_id', e.target.value)}
                  placeholder="Optional employee ID"
                />
              </div>
            </>
          )}

          {/* Student fields */}
          {formData.role === 'student' && (
            <>
              <div>
                <Label htmlFor="grade_level">Grade Level *</Label>
                <Select value={formData.grade_level} onValueChange={(value) => handleFieldChange('grade_level', value)}>
                  <SelectTrigger className={errors.grade_level ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select grade level" />
                  </SelectTrigger>
                  <SelectContent>
                    {gradeLevels.map(grade => (
                      <SelectItem key={grade} value={grade}>{grade}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.grade_level && (
                  <p className="text-sm text-red-500 mt-1">{errors.grade_level}</p>
                )}
              </div>
              
              <div>
                <Label htmlFor="student_id">Student ID</Label>
                <Input
                  id="student_id"
                  value={formData.student_id}
                  onChange={(e) => handleFieldChange('student_id', e.target.value)}
                  placeholder="Optional student ID"
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Authentication Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Authentication Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="send_invitation"
              checked={formData.send_invitation}
              onCheckedChange={(checked) => handleFieldChange('send_invitation', checked)}
            />
            <Label htmlFor="send_invitation">Send invitation email</Label>
          </div>
          
          {!formData.send_invitation && (
            <div>
              <Label htmlFor="password">Password *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
                className={errors.password ? 'border-red-500' : ''}
                placeholder="Minimum 8 characters"
              />
              {errors.password && (
                <p className="text-sm text-red-500 mt-1">{errors.password}</p>
              )}
            </div>
          )}
          
          <div className="text-sm text-gray-600">
            {formData.send_invitation 
              ? "An invitation email will be sent to the user to set up their account."
              : "The user will be created with the password you provide."
            }
          </div>
        </CardContent>
      </Card>

      {/* Form Actions */}
      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="button" variant="outline" onClick={resetForm}>
          Reset
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create User'}
        </Button>
      </div>
    </form>
  );
};