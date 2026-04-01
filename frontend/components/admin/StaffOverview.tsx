'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';

const fallbackData = {
  total: 0,
  teachers: 0,
  admin_staff: 0,
  support_staff: 0,
};

export function StaffOverview() {
  const { data, isLoading } = useQuery({
    queryKey: ['staff-stats'],
    queryFn: async () => {
      const res = await api.get('/api/v1/users/staff/stats');
      return res.data;
    },
    retry: 1,
    staleTime: 60_000,
  });

  const stats = data ?? fallbackData;
  const total = stats.total || (stats.teachers + stats.admin_staff + stats.support_staff) || 0;
  const fmt = (n: number) => new Intl.NumberFormat('en-US').format(n);

  const roles = [
    { label: 'Teachers', count: stats.teachers, color: 'bg-blue-500' },
    { label: 'Admin Staff', count: stats.admin_staff, color: 'bg-amber-500' },
    { label: 'Support Staff', count: stats.support_staff, color: 'bg-green-500' },
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Staff Overview</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-5 bg-muted animate-pulse rounded w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-green-600" />
          <CardTitle className="text-lg">Staff Overview</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-3xl font-bold">{fmt(total)}</div>

        <div className="space-y-3">
          {roles.map(({ label, count, color }) => (
            <div key={label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-medium">{fmt(count)}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full ${color} transition-all`}
                  style={{ width: total > 0 ? `${(count / total) * 100}%` : '0%' }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
