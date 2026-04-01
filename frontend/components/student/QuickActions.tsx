'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, FileText, Upload, CalendarCheck, Mail } from 'lucide-react';

const actions = [
  { label: 'View Full Timetable', href: '/student/timetable', icon: Calendar, color: 'text-blue-600' },
  { label: 'Check Grades', href: '/student/grades', icon: FileText, color: 'text-green-600' },
  { label: 'Submit Assignment', href: '/student/assignments', icon: Upload, color: 'text-orange-600' },
  { label: 'View Attendance', href: '/student/attendance', icon: CalendarCheck, color: 'text-purple-600' },
  { label: 'Contact Teacher', href: '/student/messages', icon: Mail, color: 'text-rose-600' },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-2">
          {actions.map((a) => (
            <Button key={a.href} variant="outline" size="sm" className="w-full justify-start" asChild>
              <Link href={a.href}>
                <a.icon className={`h-4 w-4 mr-2 ${a.color}`} />
                {a.label}
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
