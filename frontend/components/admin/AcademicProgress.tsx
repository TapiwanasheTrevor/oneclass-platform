'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BookOpen, TrendingUp, TrendingDown } from 'lucide-react';

const fallbackData = {
  average_grade: 0,
  highest_performing: { subject: '--', average: 0 },
  lowest_performing: { subject: '--', average: 0 },
  pass_rate: 0,
};

export function AcademicProgress() {
  const { data, isLoading } = useQuery({
    queryKey: ['academic-dashboard'],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/dashboard');
      return res.data;
    },
    retry: 1,
    staleTime: 60_000,
  });

  const stats = data ?? fallbackData;

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Academic Progress</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4].map(i => (
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
          <BookOpen className="h-5 w-5 text-purple-600" />
          <CardTitle className="text-lg">Academic Progress</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">{stats.average_grade}%</span>
          <span className="text-sm text-muted-foreground">avg. grade</span>
        </div>

        {stats.pass_rate > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Pass Rate</span>
            <Badge variant={stats.pass_rate >= 70 ? 'default' : 'destructive'}>
              {stats.pass_rate}%
            </Badge>
          </div>
        )}

        <div className="space-y-3 pt-1">
          <div className="flex items-center gap-2 text-sm">
            <TrendingUp className="h-4 w-4 text-green-600 shrink-0" />
            <span className="text-muted-foreground">Highest:</span>
            <span className="font-medium truncate">{stats.highest_performing?.subject}</span>
            {stats.highest_performing?.average > 0 && (
              <span className="ml-auto text-green-600 font-medium">
                {stats.highest_performing.average}%
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <TrendingDown className="h-4 w-4 text-red-500 shrink-0" />
            <span className="text-muted-foreground">Lowest:</span>
            <span className="font-medium truncate">{stats.lowest_performing?.subject}</span>
            {stats.lowest_performing?.average > 0 && (
              <span className="ml-auto text-red-500 font-medium">
                {stats.lowest_performing.average}%
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
