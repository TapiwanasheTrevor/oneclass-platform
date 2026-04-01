'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  UserPlus,
  UserCheck,
  Receipt,
  BarChart3,
  Settings,
} from 'lucide-react';

const actions = [
  { label: 'Add Student', href: '/admin/students/new', icon: UserPlus, color: 'text-blue-600' },
  { label: 'Add Staff', href: '/admin/staff/new', icon: UserCheck, color: 'text-green-600' },
  { label: 'Generate Invoices', href: '/admin/finance/invoices/generate', icon: Receipt, color: 'text-amber-600' },
  { label: 'View Reports', href: '/admin/reports', icon: BarChart3, color: 'text-purple-600' },
  { label: 'System Settings', href: '/admin/settings', icon: Settings, color: 'text-gray-600' },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {actions.map(({ label, href, icon: Icon, color }) => (
            <Button
              key={label}
              variant="outline"
              className="justify-start h-auto py-3 px-4"
              asChild
            >
              <Link href={href}>
                <Icon className={`h-4 w-4 mr-2 ${color}`} />
                {label}
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
