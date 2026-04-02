'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Users, UserCheck, DollarSign, CalendarCheck } from 'lucide-react';

const fallbackData = {
  total_students: 0,
  total_staff: 0,
  collection_rate: 0,
  attendance_rate: 0,
};

interface MetricCardConfig {
  key: keyof typeof fallbackData;
  label: string;
  icon: typeof Users;
  color: string;
  suffix?: string;
}

const metricCards: MetricCardConfig[] = [
  { key: 'total_students', label: 'Total Students', icon: Users, color: 'text-blue-600 bg-blue-100' },
  { key: 'total_staff', label: 'Total Staff', icon: UserCheck, color: 'text-green-600 bg-green-100' },
  { key: 'collection_rate', label: 'Collection Rate', icon: DollarSign, color: 'text-amber-600 bg-amber-100', suffix: '%' },
  { key: 'attendance_rate', label: 'Attendance Rate', icon: CalendarCheck, color: 'text-purple-600 bg-purple-100', suffix: '%' },
];

export function AdminMetrics() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard-metrics'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/dashboard');
      return res.data;
    },
    retry: 1,
    staleTime: 60_000,
  });

  const metrics = data ?? fallbackData;
  const fmt = (v: number) => new Intl.NumberFormat('en-US').format(v);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metricCards.map(({ key, label, icon: Icon, color, suffix }) => (
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
                    {fmt(metrics[key] ?? 0)}{suffix ?? ''}
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
    </div>
  );
}
