'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent } from '@/components/ui/card';
import { Users, CalendarCheck, GraduationCap, DollarSign } from 'lucide-react';

const fallbackData = {
  num_children: 0,
  avg_attendance: 0,
  avg_grade: 0,
  outstanding_fees: 0,
};

const metricCards = [
  { key: 'num_children', label: 'Children Enrolled', icon: Users, color: 'text-blue-600 bg-blue-100' },
  { key: 'avg_attendance', label: 'Avg Attendance', icon: CalendarCheck, color: 'text-green-600 bg-green-100', suffix: '%' },
  { key: 'avg_grade', label: 'Average Grade', icon: GraduationCap, color: 'text-purple-600 bg-purple-100', suffix: '%' },
  { key: 'outstanding_fees', label: 'Outstanding Fees', icon: DollarSign, color: 'text-amber-600 bg-amber-100', prefix: '$' },
] as const;

export function ParentMetrics() {
  const { user } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ['parent-dashboard-metrics', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/parent/dashboard');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const metrics = data ?? fallbackData;
  const fmt = (v: number) => new Intl.NumberFormat('en-US').format(v);

  return (
    <>
      {metricCards.map(({ key, label, icon: Icon, color, suffix, prefix }) => (
        <Card key={key}>
          <CardContent className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-lg bg-muted animate-pulse" />
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                <div className="h-7 w-16 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{label}</p>
                  <p className="text-2xl font-bold mt-1">
                    {prefix ?? ''}{fmt(metrics[key] ?? 0)}{suffix ?? ''}
                  </p>
                </div>
                <div className={`rounded-lg p-2.5 ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </>
  );
}
