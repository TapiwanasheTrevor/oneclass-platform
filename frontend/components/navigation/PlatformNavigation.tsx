// =====================================================
// Platform Navigation with Multi-Context Support
// File: frontend/components/navigation/PlatformNavigation.tsx
// =====================================================

'use client';

import React, { useState } from 'react';
import { useAuth, useSchoolContext, PlatformRole, SchoolRole } from '@/hooks/useAuth';
import { useRouter, usePathname } from 'next/navigation';
import {
  Bell,
  Settings,
  User,
  Building2,
  ChevronDown,
  Globe,
  Users,
  GraduationCap,
  BarChart3,
  DollarSign,
  FileText,
  Shield,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';

interface NavigationItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  roles?: PlatformRole[] | SchoolRole[];
  permissions?: string[];
  badge?: string;
}

export function PlatformNavigation() {
  const { user, logout, isPlatformAdmin, isSchoolAdmin } = useAuth();
  const { currentSchool, availableSchools, switchSchool, hasMultipleSchools } = useSchoolContext();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (!user) return null;

  // Get navigation items based on user context
  const getNavigationItems = (): NavigationItem[] => {
    const items: NavigationItem[] = [];

    // Super Admin Navigation
    if (isPlatformAdmin) {
      items.push(
        {
          label: 'Platform Overview',
          href: '/super-admin',
          icon: <Globe className="w-4 h-4" />,
          roles: [PlatformRole.SUPER_ADMIN]
        },
        {
          label: 'Schools Management',
          href: '/super-admin/schools',
          icon: <Building2 className="w-4 h-4" />,
          roles: [PlatformRole.SUPER_ADMIN]
        },
        {
          label: 'Platform Analytics',
          href: '/super-admin/analytics',
          icon: <BarChart3 className="w-4 h-4" />,
          roles: [PlatformRole.SUPER_ADMIN]
        },
        {
          label: 'System Settings',
          href: '/super-admin/settings',
          icon: <Settings className="w-4 h-4" />,
          roles: [PlatformRole.SUPER_ADMIN]
        }
      );
    }

    // School Context Navigation
    if (currentSchool) {
      // Dashboard
      items.push({
        label: 'Dashboard',
        href: '/dashboard',
        icon: <BarChart3 className="w-4 h-4" />
      });

      // Students Management (Admins, Registrars, Teachers)
      if (isSchoolAdmin() || currentSchool.role === SchoolRole.REGISTRAR || currentSchool.role === SchoolRole.TEACHER) {
        items.push({
          label: 'Students',
          href: '/students',
          icon: <GraduationCap className="w-4 h-4" />,
          permissions: ['students.read']
        });
      }

      // Staff Management (Admins only)
      if (isSchoolAdmin()) {
        items.push({
          label: 'Staff',
          href: '/staff',
          icon: <Users className="w-4 h-4" />,
          permissions: ['staff.read']
        });
      }

      // Finance (Admins, Bursar)
      if (isSchoolAdmin() || currentSchool.role === SchoolRole.BURSAR) {
        items.push({
          label: 'Finance',
          href: '/finance',
          icon: <DollarSign className="w-4 h-4" />,
          permissions: ['finance.read']
        });
      }

      // Analytics & Reports
      items.push({
        label: 'Analytics',
        href: '/analytics',
        icon: <BarChart3 className="w-4 h-4" />,
        permissions: ['reports.view']
      });

      // Academic Module (Teachers, Academic Head)
      if (currentSchool.role === SchoolRole.TEACHER || 
          currentSchool.role === SchoolRole.ACADEMIC_HEAD ||
          isSchoolAdmin()) {
        items.push({
          label: 'Academic',
          href: '/academic',
          icon: <FileText className="w-4 h-4" />,
          permissions: ['academic.read']
        });
      }

      // Parent Portal
      if (currentSchool.role === SchoolRole.PARENT) {
        items.push(
          {
            label: 'My Children',
            href: '/parent/children',
            icon: <Users className="w-4 h-4" />
          },
          {
            label: 'Payments',
            href: '/parent/payments',
            icon: <DollarSign className="w-4 h-4" />
          }
        );
      }

      // Student Portal
      if (currentSchool.role === SchoolRole.STUDENT) {
        items.push(
          {
            label: 'My Classes',
            href: '/student/classes',
            icon: <GraduationCap className="w-4 h-4" />
          },
          {
            label: 'Assignments',
            href: '/student/assignments',
            icon: <FileText className="w-4 h-4" />
          }
        );
      }

      // Settings (Admins)
      if (isSchoolAdmin()) {
        items.push({
          label: 'Settings',
          href: '/settings',
          icon: <Settings className="w-4 h-4" />,
          permissions: ['settings.manage']
        });
      }
    }

    return items;
  };

  const navigationItems = getNavigationItems();

  const handleSchoolSwitch = (schoolId: string) => {
    switchSchool(schoolId);
    router.refresh();
  };

  const getUserDisplayName = () => {
    return `${user.first_name} ${user.last_name}`;
  };

  const getUserInitials = () => {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
  };

  const getRoleDisplayName = () => {
    if (isPlatformAdmin) return 'Platform Administrator';
    if (!currentSchool) return user.platform_role.replace('_', ' ').toUpperCase();
    
    const schoolRole = currentSchool.role.replace('_', ' ').toLowerCase()
      .replace(/\b\w/g, l => l.toUpperCase());
    return `${schoolRole} at ${currentSchool.school_name}`;
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Logo and Brand */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">OC</span>
            </div>
            <span className="text-xl font-bold text-gray-900">OneClass</span>
          </div>
          
          {/* Current Context Indicator */}
          {currentSchool && (
            <>
              <Separator orientation="vertical" className="h-6" />
              <div className="text-sm text-gray-600">
                <span className="font-medium">{currentSchool.school_name}</span>
              </div>
            </>
          )}
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-6">
          {navigationItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === item.href
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.badge && (
                <Badge variant="secondary" className="ml-1">
                  {item.badge}
                </Badge>
              )}
            </a>
          ))}
        </div>

        {/* Right Side - User Controls */}
        <div className="flex items-center space-x-4">
          {/* School Switcher */}
          {hasMultipleSchools && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Building2 className="w-4 h-4 mr-2" />
                  Switch School
                  <ChevronDown className="w-4 h-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64">
                <DropdownMenuLabel>Available Schools</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {availableSchools.map((school) => (
                  <DropdownMenuItem
                    key={school.school_id}
                    onClick={() => handleSchoolSwitch(school.school_id)}
                    className={currentSchool?.school_id === school.school_id ? 'bg-blue-50' : ''}
                  >
                    <div className="flex flex-col">
                      <span className="font-medium">{school.school_name}</span>
                      <span className="text-sm text-gray-500">
                        {school.role.replace('_', ' ').toLowerCase()}
                      </span>
                    </div>
                    {currentSchool?.school_id === school.school_id && (
                      <Badge variant="default" className="ml-auto">Current</Badge>
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* Notifications */}
          <Button variant="ghost" size="sm">
            <Bell className="w-4 h-4" />
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.profile?.profile_image_url} alt={getUserDisplayName()} />
                  <AvatarFallback>{getUserInitials()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{getUserDisplayName()}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user.email}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {getRoleDisplayName()}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push('/profile')}>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/settings')}>
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </DropdownMenuItem>
              {isPlatformAdmin && (
                <DropdownMenuItem onClick={() => router.push('/super-admin')}>
                  <Shield className="mr-2 h-4 w-4" />
                  <span>Super Admin</span>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Mobile Menu Toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-4 pb-4 border-t border-gray-200">
          <div className="space-y-2 pt-4">
            {navigationItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.href
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.icon}
                <span>{item.label}</span>
                {item.badge && (
                  <Badge variant="secondary" className="ml-auto">
                    {item.badge}
                  </Badge>
                )}
              </a>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}