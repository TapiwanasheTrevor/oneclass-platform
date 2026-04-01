'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ClipboardCheck, FileText, Users, FilePlus, Calendar } from 'lucide-react';
import Link from 'next/link';

const actions = [
  { label: 'Mark Attendance', href: '/staff/attendance', icon: ClipboardCheck, color: 'text-blue-600' },
  { label: 'Enter Grades', href: '/staff/grades', icon: FileText, color: 'text-green-600' },
  { label: 'View Class List', href: '/staff/classes', icon: Users, color: 'text-purple-600' },
  { label: 'Create Assessment', href: '/staff/assessments/new', icon: FilePlus, color: 'text-amber-600' },
  { label: 'View Timetable', href: '/staff/timetable', icon: Calendar, color: 'text-rose-600' },
] as const;

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {actions.map(({ label, href, icon: Icon, color }) => (
            <Button key={href} variant="outline" className="justify-start gap-2 h-10" asChild>
              <Link href={href}>
                <Icon className={`h-4 w-4 ${color}`} />
                {label}
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
