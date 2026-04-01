'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar, MapPin } from 'lucide-react';

interface Period {
  id: string;
  period_number: number;
  start_time: string;
  end_time: string;
  subject: string;
  class_name: string;
  room: string;
  is_current: boolean;
}

const fallback: Period[] = [];

export function TodaySchedule() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['today-schedule', user?.id],
    queryFn: async () => (await api.get('/api/v1/academic/timetable/today')).data as Period[],
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const periods = data ?? fallback;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Calendar className="h-5 w-5" /> Today&apos;s Schedule
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        ) : periods.length === 0 ? (
          <p className="text-sm text-muted-foreground">No periods scheduled for today.</p>
        ) : (
          <div className="space-y-2">
            {periods.map(p => (
              <div
                key={p.id}
                className={`flex items-center gap-4 rounded-lg border p-3 ${
                  p.is_current ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : ''
                }`}
              >
                <div className="text-center min-w-[60px]">
                  <p className="text-xs font-medium text-muted-foreground">Period {p.period_number}</p>
                  <p className="text-xs text-muted-foreground">{p.start_time}&ndash;{p.end_time}</p>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">{p.subject}</p>
                  <p className="text-xs text-muted-foreground">{p.class_name}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3" /> {p.room}
                  </span>
                  {p.is_current && <Badge>Now</Badge>}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
