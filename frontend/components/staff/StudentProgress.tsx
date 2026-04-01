'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, AlertTriangle } from 'lucide-react';

interface ClassProgress {
  class_name: string;
  subject: string;
  average: number;
  students_below_pass: number;
  total_students: number;
}

interface ProgressData {
  classes: ClassProgress[];
  students_needing_attention: { name: string; class_name: string; average: number }[];
}

const fallback: ProgressData = { classes: [], students_needing_attention: [] };

export function StudentProgress() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['student-progress', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/teacher/student-progress')).data as ProgressData,
    enabled: !!user,
    retry: 1,
    staleTime: 120_000,
  });

  const progress = data ?? fallback;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="h-5 w-5" /> Student Progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : progress.classes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No progress data available.</p>
        ) : (
          <>
            {progress.classes.map(c => (
              <div key={c.class_name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{c.class_name} &ndash; {c.subject}</span>
                  <span className={c.average < 50 ? 'text-destructive' : ''}>{c.average}%</span>
                </div>
                <Progress value={c.average} className="h-2" />
                {c.students_below_pass > 0 && (
                  <p className="text-xs text-destructive mt-1">
                    {c.students_below_pass} of {c.total_students} below 50%
                  </p>
                )}
              </div>
            ))}
            {progress.students_needing_attention.length > 0 && (
              <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                <p className="flex items-center gap-1 text-sm font-medium text-destructive mb-2">
                  <AlertTriangle className="h-4 w-4" /> Needs Attention
                </p>
                <div className="space-y-1">
                  {progress.students_needing_attention.slice(0, 5).map(s => (
                    <div key={s.name} className="flex justify-between text-xs">
                      <span>{s.name} <span className="text-muted-foreground">({s.class_name})</span></span>
                      <Badge variant="destructive" className="text-[10px] px-1.5">{s.average}%</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
