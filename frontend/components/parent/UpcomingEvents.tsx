'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar, Trophy, BookOpen, Users, Sun } from 'lucide-react';

interface SchoolEvent {
  id: string;
  title: string;
  date: string;
  type: string;
}

const typeConfig: Record<string, { icon: typeof Calendar; color: string }> = {
  meeting: { icon: Users, color: 'bg-blue-100 text-blue-700' },
  exam: { icon: BookOpen, color: 'bg-red-100 text-red-700' },
  holiday: { icon: Sun, color: 'bg-amber-100 text-amber-700' },
  sports: { icon: Trophy, color: 'bg-green-100 text-green-700' },
};

export function UpcomingEvents() {
  const { user } = useAuth();

  const { data: events = [], isLoading } = useQuery<SchoolEvent[]>({
    queryKey: ['parent-upcoming-events', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/academic/events/upcoming');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" /> Upcoming Events
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))
        ) : events.length === 0 ? (
          <p className="text-sm text-muted-foreground">No upcoming events.</p>
        ) : (
          events.map((event) => {
            const config = typeConfig[event.type] ?? { icon: Calendar, color: 'bg-muted text-muted-foreground' };
            const Icon = config.icon;
            return (
              <div key={event.id} className="flex items-start gap-3">
                <div className={`rounded p-1.5 ${config.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{event.title}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(event.date)}</p>
                </div>
                <Badge variant="outline" className="text-xs shrink-0">{event.type}</Badge>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
