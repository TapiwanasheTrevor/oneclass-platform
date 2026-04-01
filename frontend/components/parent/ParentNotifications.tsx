'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Bell, DollarSign, GraduationCap, AlertTriangle, Info } from 'lucide-react';

interface Notification {
  id: string;
  type: string;
  message: string;
  created_at: string;
  is_read: boolean;
}

const typeIcons: Record<string, typeof Bell> = {
  fee_reminder: DollarSign,
  grade_update: GraduationCap,
  attendance_alert: AlertTriangle,
  info: Info,
};

export function ParentNotifications() {
  const { user } = useAuth();

  const { data: notifications = [], isLoading } = useQuery<Notification[]>({
    queryKey: ['parent-notifications', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications/recent');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 30_000,
  });

  const timeAgo = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Bell className="h-5 w-5" /> Notifications
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
          ))
        ) : notifications.length === 0 ? (
          <p className="text-sm text-muted-foreground">No new notifications.</p>
        ) : (
          notifications.slice(0, 5).map((n) => {
            const Icon = typeIcons[n.type] ?? Bell;
            return (
              <div key={n.id} className={`flex items-start gap-3 rounded-md p-2 ${n.is_read ? '' : 'bg-muted/50'}`}>
                <div className="rounded-full bg-primary/10 p-1.5 mt-0.5">
                  <Icon className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${n.is_read ? '' : 'font-medium'}`}>{n.message}</p>
                  <p className="text-xs text-muted-foreground">{timeAgo(n.created_at)}</p>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
