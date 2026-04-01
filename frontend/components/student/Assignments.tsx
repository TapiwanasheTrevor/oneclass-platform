'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ClipboardList } from 'lucide-react';

interface Assignment {
  id: string;
  subject: string;
  title: string;
  due_date: string;
  status: 'pending' | 'submitted' | 'overdue' | 'graded';
}

const fallbackData: Assignment[] = [
  { id: '1', subject: 'Mathematics', title: 'Quadratic Equations Worksheet', due_date: '2026-04-03', status: 'pending' },
  { id: '2', subject: 'English', title: 'Book Review Essay', due_date: '2026-04-05', status: 'pending' },
  { id: '3', subject: 'Science', title: 'Lab Report: Photosynthesis', due_date: '2026-03-30', status: 'overdue' },
  { id: '4', subject: 'History', title: 'Colonial Era Timeline', due_date: '2026-04-07', status: 'submitted' },
];

function statusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'submitted' || status === 'graded') return 'secondary';
  if (status === 'overdue') return 'destructive';
  return 'outline';
}

export function Assignments() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['pending-assignments', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/assignments/pending');
      return res.data as Assignment[];
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 60_000,
  });

  const assignments = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5" />
          Assignments
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : (
          <div className="space-y-2">
            {assignments.map((a) => {
              const isOverdue = a.status === 'overdue' || (a.status === 'pending' && new Date(a.due_date) < new Date());
              const effectiveStatus = isOverdue && a.status === 'pending' ? 'overdue' : a.status;
              return (
                <div key={a.id} className={`flex items-center justify-between rounded-lg border p-3 ${isOverdue ? 'border-red-300 bg-red-50' : ''}`}>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-sm">{a.title}</p>
                    <p className="text-xs text-muted-foreground">{a.subject}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground">Due {new Date(a.due_date).toLocaleDateString()}</span>
                    <Badge variant={statusVariant(effectiveStatus)}>
                      {effectiveStatus}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
