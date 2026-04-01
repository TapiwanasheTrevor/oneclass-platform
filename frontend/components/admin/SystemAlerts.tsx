'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle } from 'lucide-react';

interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  details?: string;
}

const severityStyle: Record<string, string> = {
  error: 'border-red-200 bg-red-50 text-red-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
};

const badgeVariant: Record<string, 'destructive' | 'secondary' | 'outline'> = {
  error: 'destructive',
  warning: 'secondary',
  info: 'outline',
};

export function SystemAlerts() {
  const { data, isLoading } = useQuery({
    queryKey: ['system-alerts'],
    queryFn: async () => {
      const res = await api.get('/api/v1/monitoring/alerts');
      return res.data as Alert[];
    },
    retry: 1,
    staleTime: 60_000,
  });

  const alerts: Alert[] = data ?? [];

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">System Alerts</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 bg-muted animate-pulse rounded" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <CardTitle className="text-lg">System Alerts</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="flex items-center gap-2 py-4 justify-center text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-600" />
            No alerts -- all systems operational.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`rounded-md border p-3 text-sm ${severityStyle[alert.type] ?? severityStyle.info}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span>{alert.message}</span>
                  <Badge variant={badgeVariant[alert.type] ?? 'outline'} className="shrink-0">
                    {alert.type}
                  </Badge>
                </div>
                {alert.details && (
                  <p className="mt-1 text-xs opacity-80">{alert.details}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
