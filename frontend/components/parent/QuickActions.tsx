'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, DollarSign, MessageSquare, CalendarDays, School } from 'lucide-react';
import Link from 'next/link';

const actions = [
  { label: 'Report Cards', href: '/parent/reports', icon: FileText, color: 'text-blue-600' },
  { label: 'Pay Fees', href: '/parent/fees', icon: DollarSign, color: 'text-green-600' },
  { label: 'Contact Teacher', href: '/parent/messages/new', icon: MessageSquare, color: 'text-purple-600' },
  { label: 'View Schedule', href: '/parent/schedule', icon: CalendarDays, color: 'text-amber-600' },
  { label: 'School Calendar', href: '/parent/calendar', icon: School, color: 'text-red-600' },
] as const;

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
          {actions.map(({ label, href, icon: Icon, color }) => (
            <Button key={label} variant="outline" className="h-auto flex-col gap-2 py-4" asChild>
              <Link href={href}>
                <Icon className={`h-5 w-5 ${color}`} />
                <span className="text-xs font-medium">{label}</span>
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
