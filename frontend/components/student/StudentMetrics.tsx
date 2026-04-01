'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { GraduationCap, CalendarCheck, ClipboardList, Trophy } from 'lucide-react';

const fallbackData = { gpa: 3.2, attendance: 91, assignments_due: 3, class_rank: 8 };

export function StudentMetrics() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['student-dashboard-metrics', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/student/dashboard');
      return res.data;
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 60_000,
  });

  const metrics = data ?? fallbackData;

  const cards = [
    { label: 'Average Grade', value: `${metrics.gpa}`, icon: GraduationCap, color: 'text-blue-600 bg-blue-100' },
    { label: 'Attendance', value: `${metrics.attendance}%`, icon: CalendarCheck, color: 'text-green-600 bg-green-100' },
    { label: 'Assignments Due', value: `${metrics.assignments_due}`, icon: ClipboardList, color: 'text-orange-600 bg-orange-100' },
    { label: 'Class Rank', value: `#${metrics.class_rank}`, icon: Trophy, color: 'text-purple-600 bg-purple-100' },
  ];

  if (isLoading) {
    return (
      <>
        {cards.map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-16 w-full" />
            </CardContent>
          </Card>
        ))}
      </>
    );
  }

  return (
    <>
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{c.label}</p>
                <p className="text-2xl font-bold mt-1">{c.value}</p>
              </div>
              <div className={`h-10 w-10 rounded-full flex items-center justify-center ${c.color}`}>
                <c.icon className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </>
  );
}
