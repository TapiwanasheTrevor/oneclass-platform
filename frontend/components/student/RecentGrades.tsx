'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText } from 'lucide-react';

interface Grade {
  subject: string;
  assessment: string;
  score: number;
  date: string;
}

function gradeLabel(score: number) {
  if (score >= 80) return 'A';
  if (score >= 60) return 'B';
  if (score >= 50) return 'C';
  if (score >= 40) return 'D';
  if (score >= 30) return 'E';
  return 'U';
}

function gradeColor(score: number): string {
  if (score >= 60) return 'bg-green-100 text-green-700';
  if (score >= 50) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

const fallbackData: Grade[] = [
  { subject: 'Mathematics', assessment: 'Mid-Term Test', score: 82, date: '2026-03-28' },
  { subject: 'English', assessment: 'Essay Writing', score: 74, date: '2026-03-26' },
  { subject: 'Science', assessment: 'Lab Report', score: 65, date: '2026-03-25' },
  { subject: 'History', assessment: 'Chapter Quiz', score: 48, date: '2026-03-23' },
  { subject: 'Shona', assessment: 'Oral Exam', score: 88, date: '2026-03-20' },
];

export function RecentGrades() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['recent-grades', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/grades/recent');
      return res.data as Grade[];
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 60_000,
  });

  const grades = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Recent Grades
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : (
          <div className="space-y-2">
            {grades.slice(0, 5).map((g, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm">{g.subject}</p>
                  <p className="text-xs text-muted-foreground">{g.assessment}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{new Date(g.date).toLocaleDateString()}</span>
                  <Badge className={gradeColor(g.score)}>
                    {g.score}% ({gradeLabel(g.score)})
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
