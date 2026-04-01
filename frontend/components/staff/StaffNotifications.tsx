'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Bell, CalendarClock, Megaphone, AlertCircle, Info } from 'lucide-react';

interface Notification {
  id: string;
  type: 'schedule_change' | 'announcement' | 'student_alert' | 'info';
  message: string;
  time: string;
  read: boolean;
}

const iconMap = {
  schedule_change: CalendarClock,
  announcement: Megaphone,
  student_alert: AlertCircle,
  info: Info,
};

const fallback: Notification[] = [];

export function StaffNotifications() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['staff-notifications', user?.id],
    queryFn: async () => (await api.get('/api/v1/notifications/recent')).data as Notification[],
    enabled: !!user,
    retry: 1,
    staleTime: 30_000,
  });

  const notifications = (data ?? fallback).slice(0, 5);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Bell className="h-5 w-5" /> Notifications
          {notifications.filter(n => !n.read).length > 0 && (
            <Badge className="ml-auto">{notifications.filter(n => !n.read).length} new</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : notifications.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent notifications.</p>
        ) : (
          <div className="space-y-2">
            {notifications.map(n => {
              const Icon = iconMap[n.type] ?? Info;
              return (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 rounded-lg p-2.5 ${!n.read ? 'bg-muted/50' : ''}`}
                >
                  <div className="mt-0.5 rounded-full bg-muted p-1.5">
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-snug">{n.message}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{n.time}</p>
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
