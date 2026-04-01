'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { GraduationCap } from 'lucide-react';

const fallbackData = {
  total_enrolled: 0,
  male: 0,
  female: 0,
  by_grade: [] as { grade: string; count: number }[],
};

export function StudentMetrics() {
  const { data, isLoading } = useQuery({
    queryKey: ['student-stats'],
    queryFn: async () => {
      const res = await api.get('/api/v1/sis/students/stats');
      return res.data;
    },
    retry: 1,
    staleTime: 60_000,
  });

  const stats = data ?? fallbackData;
  const total = stats.total_enrolled || (stats.male + stats.female) || 0;
  const malePercent = total > 0 ? Math.round((stats.male / total) * 100) : 50;
  const fmt = (n: number) => new Intl.NumberFormat('en-US').format(n);

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Student Enrollment</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-4 bg-muted animate-pulse rounded w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-5 w-5 text-blue-600" />
          <CardTitle className="text-lg">Student Enrollment</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-3xl font-bold">{fmt(total)}</div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span>Male: {fmt(stats.male)}</span>
            <span>Female: {fmt(stats.female)}</span>
          </div>
          <div className="flex h-3 w-full rounded-full overflow-hidden bg-muted">
            <div className="bg-blue-500 transition-all" style={{ width: `${malePercent}%` }} />
            <div className="bg-pink-500 transition-all" style={{ width: `${100 - malePercent}%` }} />
          </div>
        </div>

        {stats.by_grade?.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-sm font-medium text-muted-foreground">By Grade</p>
            {stats.by_grade.slice(0, 6).map((g: { grade: string; count: number }) => (
              <div key={g.grade} className="flex items-center justify-between text-sm">
                <span>{g.grade}</span>
                <span className="font-medium">{fmt(g.count)}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
