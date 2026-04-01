'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { CalendarCheck } from 'lucide-react';

interface ChildAttendance {
  child_id: string;
  child_name: string;
  attendance_percentage: number;
  days_present: number;
  days_absent: number;
  total_days: number;
}

export function AttendanceTracking() {
  const { user } = useAuth();

  const { data: attendance = [], isLoading } = useQuery<ChildAttendance[]>({
    queryKey: ['parent-children-attendance', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/parent/children/attendance');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <CalendarCheck className="h-5 w-5" /> Attendance Tracking
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))
        ) : attendance.length === 0 ? (
          <p className="text-sm text-muted-foreground">No attendance data available yet.</p>
        ) : (
          attendance.map((child) => {
            const isLow = child.attendance_percentage < 80;
            return (
              <div key={child.child_id} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{child.child_name}</span>
                  <span className={isLow ? 'text-red-600 font-semibold' : 'text-green-600 font-semibold'}>
                    {child.attendance_percentage.toFixed(1)}%
                  </span>
                </div>
                <Progress value={child.attendance_percentage} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  {child.days_present} present / {child.days_absent} absent of {child.total_days} days
                  {isLow && <span className="ml-2 text-red-500 font-medium">Below 80% threshold</span>}
                </p>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
