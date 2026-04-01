'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ClipboardCheck, Users } from 'lucide-react';
import Link from 'next/link';

interface CurrentSession {
  class_name: string;
  subject: string;
  period: number;
  student_count: number;
  attendance_marked: boolean;
}

export function AttendanceQuickEntry() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['current-session', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/teacher/current-session')).data as CurrentSession | null,
    enabled: !!user,
    retry: 1,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <ClipboardCheck className="h-5 w-5" /> Attendance
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : !data ? (
          <p className="text-sm text-muted-foreground">No active session right now.</p>
        ) : (
          <div className="space-y-3">
            <div>
              <p className="font-medium text-sm">{data.subject} &middot; Period {data.period}</p>
              <p className="text-xs text-muted-foreground">{data.class_name}</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" /> {data.student_count} students
              {data.attendance_marked ? (
                <Badge variant="secondary" className="ml-auto">Marked</Badge>
              ) : (
                <Badge variant="destructive" className="ml-auto">Pending</Badge>
              )}
            </div>
            <Button asChild className="w-full" disabled={data.attendance_marked}>
              <Link href="/staff/attendance">
                {data.attendance_marked ? 'View Attendance' : 'Mark Attendance'}
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
