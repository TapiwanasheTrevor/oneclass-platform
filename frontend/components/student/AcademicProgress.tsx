'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp } from 'lucide-react';

interface SubjectProgress {
  subject: string;
  percentage: number;
}

const fallbackData: SubjectProgress[] = [
  { subject: 'Mathematics', percentage: 82 },
  { subject: 'English', percentage: 74 },
  { subject: 'Science', percentage: 88 },
  { subject: 'History', percentage: 65 },
  { subject: 'Shona', percentage: 91 },
  { subject: 'Geography', percentage: 70 },
];

function barColor(pct: number): string {
  if (pct >= 80) return 'bg-green-500';
  if (pct >= 60) return 'bg-blue-500';
  if (pct >= 50) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function AcademicProgress() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['academic-progress', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/student/progress');
      return res.data as SubjectProgress[];
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 5 * 60_000,
  });

  const subjects = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Academic Progress
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        ) : (
          <div className="space-y-3">
            {subjects.map((s) => (
              <div key={s.subject}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{s.subject}</span>
                  <span className="font-medium">{s.percentage}%</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-secondary overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(s.percentage)}`}
                    style={{ width: `${s.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
