'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent } from '@/components/ui/card';
import { BookOpen, Users, TrendingUp, Clock } from 'lucide-react';

const fallback = { my_classes: 0, total_students: 0, avg_performance: 0, todays_periods: 0 };

interface MetricCardConfig {
  key: keyof typeof fallback;
  label: string;
  icon: typeof BookOpen;
  color: string;
  suffix?: string;
}

const cards: MetricCardConfig[] = [
  { key: 'my_classes', label: 'My Classes', icon: BookOpen, color: 'text-blue-600 bg-blue-100' },
  { key: 'total_students', label: 'Total Students', icon: Users, color: 'text-green-600 bg-green-100' },
  { key: 'avg_performance', label: 'Avg Performance', icon: TrendingUp, color: 'text-amber-600 bg-amber-100', suffix: '%' },
  { key: 'todays_periods', label: "Today's Periods", icon: Clock, color: 'text-purple-600 bg-purple-100' },
];

export function StaffMetrics() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['staff-dashboard-metrics', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/teacher/dashboard')).data,
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const m = data ?? fallback;

  return (
    <>
      {cards.map(({ key, label, icon: Icon, color, suffix }) => (
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
                    {m[key] ?? 0}{suffix ?? ''}
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
