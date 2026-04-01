'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { BookOpen } from 'lucide-react';

interface ChildAcademic {
  child_id: string;
  child_name: string;
  average_grade: number;
  best_subject: string;
  worst_subject: string;
  total_subjects: number;
}

export function AcademicProgress() {
  const { user } = useAuth();

  const { data: academics = [], isLoading } = useQuery<ChildAcademic[]>({
    queryKey: ['parent-children-academic', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/parent/children/academic');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const gradeColor = (avg: number) => {
    if (avg >= 80) return 'bg-green-100 text-green-700';
    if (avg >= 60) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <BookOpen className="h-5 w-5" /> Academic Progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-full" />
            </div>
          ))
        ) : academics.length === 0 ? (
          <p className="text-sm text-muted-foreground">No academic data available yet.</p>
        ) : (
          academics.map((child) => (
            <div key={child.child_id} className="rounded-md border p-3 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{child.child_name}</p>
                <Badge className={gradeColor(child.average_grade)}>
                  {child.average_grade.toFixed(1)}%
                </Badge>
              </div>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>Best: <span className="text-green-600 font-medium">{child.best_subject}</span></span>
                <span>Weakest: <span className="text-red-600 font-medium">{child.worst_subject}</span></span>
              </div>
              <p className="text-xs text-muted-foreground">{child.total_subjects} subjects</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
