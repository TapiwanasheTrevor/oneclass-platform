'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Bell, GraduationCap, CalendarDays, Megaphone, Info } from 'lucide-react';

interface Notification {
  id: string;
  type: 'announcement' | 'grade' | 'schedule' | 'general';
  message: string;
  created_at: string;
}

const typeIcons: Record<string, typeof Bell> = {
  announcement: Megaphone,
  grade: GraduationCap,
  schedule: CalendarDays,
  general: Info,
};

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

const fallbackData: Notification[] = [
  { id: '1', type: 'grade', message: 'Mathematics mid-term results have been published', created_at: '2026-03-31T14:00:00Z' },
  { id: '2', type: 'announcement', message: 'School sports day scheduled for next Friday', created_at: '2026-03-31T09:00:00Z' },
  { id: '3', type: 'schedule', message: 'Science class moved to Lab 2 tomorrow', created_at: '2026-03-30T15:30:00Z' },
  { id: '4', type: 'general', message: 'Library books due for return by end of week', created_at: '2026-03-29T10:00:00Z' },
  { id: '5', type: 'announcement', message: 'Parent-teacher conference on April 10th', created_at: '2026-03-28T08:00:00Z' },
];

export function StudentNotifications() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['student-notifications', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications/recent');
      return res.data as Notification[];
    },
    enabled: !!user?.id,
    retry: 1,
    staleTime: 60_000,
  });

  const notifications = data ?? fallbackData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Notifications
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.slice(0, 5).map((n) => {
              const Icon = typeIcons[n.type] ?? Bell;
              return (
                <div key={n.id} className="flex items-start gap-3 rounded-lg border p-3">
                  <div className="mt-0.5 shrink-0">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">{n.message}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{relativeTime(n.created_at)}</p>
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
