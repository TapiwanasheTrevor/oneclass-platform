'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Clock } from 'lucide-react';

interface Period {
  period: number;
  start_time: string;
  end_time: string;
  subject: string;
  teacher: string;
  room: string;
}

const fallbackData: Period[] = [
  { period: 1, start_time: '07:30', end_time: '08:10', subject: 'Mathematics', teacher: 'Mr. Moyo', room: 'A12' },
  { period: 2, start_time: '08:15', end_time: '08:55', subject: 'English', teacher: 'Mrs. Ndlovu', room: 'B3' },
  { period: 3, start_time: '09:00', end_time: '09:40', subject: 'Science', teacher: 'Mr. Chikwanha', room: 'Lab 1' },
  { period: 4, start_time: '10:00', end_time: '10:40', subject: 'History', teacher: 'Ms. Mapfumo', room: 'C7' },
  { period: 5, start_time: '10:45', end_time: '11:25', subject: 'Geography', teacher: 'Mr. Sibanda', room: 'C5' },
  { period: 6, start_time: '11:30', end_time: '12:10', subject: 'Shona', teacher: 'Mrs. Mutasa', room: 'A8' },
];

export function ClassSchedule() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['class-schedule-today', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/timetable/today');
      return res.data as Period[];
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 5 * 60_000,
  });

  const periods = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Today&apos;s Schedule
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : (
          <div className="space-y-2">
            {periods.map((p) => (
              <div key={p.period} className="flex items-center gap-4 rounded-lg border p-3">
                <div className="text-sm font-mono text-muted-foreground w-28 shrink-0">
                  {p.start_time} - {p.end_time}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{p.subject}</p>
                  <p className="text-xs text-muted-foreground">{p.teacher}</p>
                </div>
                <Badge variant="outline">{p.room}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
