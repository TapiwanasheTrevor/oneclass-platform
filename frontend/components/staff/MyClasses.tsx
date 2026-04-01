'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { BookOpen, Users, Clock } from 'lucide-react';

interface TeacherClass {
  id: string;
  subject: string;
  grade_level: string;
  class_name: string;
  student_count: number;
  next_session?: string;
}

const fallback: TeacherClass[] = [];

export function MyClasses() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['teacher-classes', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/teacher/classes')).data as TeacherClass[],
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const classes = data ?? fallback;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <BookOpen className="h-5 w-5" /> My Classes
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
          </div>
        ) : classes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No classes assigned yet.</p>
        ) : (
          <div className="space-y-3">
            {classes.map(c => (
              <div key={c.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium text-sm">{c.subject}</p>
                  <p className="text-xs text-muted-foreground">{c.class_name} &middot; {c.grade_level}</p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <Users className="h-3.5 w-3.5" /> {c.student_count}
                  </span>
                  {c.next_session && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {c.next_session}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
