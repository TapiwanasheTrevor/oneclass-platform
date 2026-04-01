'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { CalendarCheck } from 'lucide-react';

interface AttendanceSummary {
  present_days: number;
  absent_days: number;
  late_days: number;
  total_days: number;
  attendance_percentage: number;
}

const fallbackData: AttendanceSummary = {
  present_days: 42,
  absent_days: 3,
  late_days: 2,
  total_days: 47,
  attendance_percentage: 89.4,
};

export function AttendanceOverview() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['attendance-summary', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/attendance/summary');
      return res.data as AttendanceSummary;
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 5 * 60_000,
  });

  const summary = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarCheck className="h-5 w-5" />
          Attendance
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Attendance Rate</span>
                <span className="font-semibold">{summary.attendance_percentage.toFixed(1)}%</span>
              </div>
              <Progress value={summary.attendance_percentage} className="h-3" />
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="rounded-lg bg-green-50 p-3">
                <p className="text-lg font-bold text-green-700">{summary.present_days}</p>
                <p className="text-xs text-muted-foreground">Present</p>
              </div>
              <div className="rounded-lg bg-red-50 p-3">
                <p className="text-lg font-bold text-red-700">{summary.absent_days}</p>
                <p className="text-xs text-muted-foreground">Absent</p>
              </div>
              <div className="rounded-lg bg-yellow-50 p-3">
                <p className="text-lg font-bold text-yellow-700">{summary.late_days}</p>
                <p className="text-xs text-muted-foreground">Late</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
