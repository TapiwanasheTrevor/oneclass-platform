'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText } from 'lucide-react';

interface GradeSummary {
  recent_assessments: { title: string; class_name: string; date: string; graded: number; total: number }[];
  overall_graded: number;
  overall_total: number;
  class_averages: { class_name: string; average: number }[];
}

const fallback: GradeSummary = { recent_assessments: [], overall_graded: 0, overall_total: 0, class_averages: [] };

export function GradeBookSummary() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['grade-summary', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/teacher/grades/summary')).data as GradeSummary,
    enabled: !!user,
    retry: 1,
    staleTime: 120_000,
  });

  const summary = data ?? fallback;
  const pct = summary.overall_total > 0 ? Math.round((summary.overall_graded / summary.overall_total) * 100) : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5" /> Gradebook Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : (
          <>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">Grading progress</span>
                <span className="font-medium">{summary.overall_graded}/{summary.overall_total}</span>
              </div>
              <Progress value={pct} className="h-2" />
            </div>
            {summary.recent_assessments.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Recent Assessments</p>
                {summary.recent_assessments.slice(0, 4).map(a => (
                  <div key={a.title + a.class_name} className="flex items-center justify-between rounded border p-2">
                    <div>
                      <p className="text-sm font-medium">{a.title}</p>
                      <p className="text-xs text-muted-foreground">{a.class_name} &middot; {a.date}</p>
                    </div>
                    <Badge variant={a.graded === a.total ? 'secondary' : 'destructive'}>
                      {a.graded}/{a.total}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
            {summary.class_averages.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Class Averages</p>
                {summary.class_averages.map(c => (
                  <div key={c.class_name} className="flex justify-between text-sm">
                    <span>{c.class_name}</span>
                    <span className="font-medium">{c.average}%</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
