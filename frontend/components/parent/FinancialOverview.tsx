'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, CreditCard, CalendarClock } from 'lucide-react';

interface FinanceSummary {
  total_outstanding: number;
  total_paid: number;
  next_due_date: string | null;
  recent_payments: { id: string; amount: number; date: string; description: string }[];
}

const fallback: FinanceSummary = {
  total_outstanding: 0,
  total_paid: 0,
  next_due_date: null,
  recent_payments: [],
};

export function FinancialOverview() {
  const { user } = useAuth();

  const { data, isLoading } = useQuery<FinanceSummary>({
    queryKey: ['parent-finance-summary', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/finance/parent/summary');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  const summary = data ?? fallback;
  const usd = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);
  const fmtDate = (d: string | null) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <DollarSign className="h-5 w-5" /> Financial Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-full" />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">Outstanding</p>
                <p className="text-lg font-bold text-red-600">{usd(summary.total_outstanding)}</p>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-xs text-muted-foreground">Total Paid</p>
                <p className="text-lg font-bold text-green-600">{usd(summary.total_paid)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarClock className="h-4 w-4" />
              <span>Next due: <span className="font-medium text-foreground">{fmtDate(summary.next_due_date)}</span></span>
            </div>
            {summary.recent_payments.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Recent Payments</p>
                {summary.recent_payments.slice(0, 3).map((p) => (
                  <div key={p.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <CreditCard className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="truncate max-w-[160px]">{p.description}</span>
                    </div>
                    <span className="font-medium">{usd(p.amount)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
