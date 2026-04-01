'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { DollarSign } from 'lucide-react';

const fallbackData = {
  total_invoiced: 0,
  total_collected: 0,
  total_outstanding: 0,
  collection_rate: 0,
};

const usd = (amount: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

export function FinancialSummary() {
  const { data, isLoading } = useQuery({
    queryKey: ['finance-dashboard'],
    queryFn: async () => {
      const res = await api.get('/api/v1/finance/dashboard');
      return res.data;
    },
    retry: 1,
    staleTime: 60_000,
  });

  const finance = data ?? fallbackData;
  const rate = finance.collection_rate ?? (
    finance.total_invoiced > 0
      ? Math.round((finance.total_collected / finance.total_invoiced) * 100)
      : 0
  );

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-lg">Financial Summary</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-5 bg-muted animate-pulse rounded w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const rows = [
    { label: 'Total Invoiced', value: usd(finance.total_invoiced), color: 'text-foreground' },
    { label: 'Total Collected', value: usd(finance.total_collected), color: 'text-green-600' },
    { label: 'Outstanding', value: usd(finance.total_outstanding), color: 'text-red-600' },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-amber-600" />
          <CardTitle className="text-lg">Financial Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map(({ label, value, color }) => (
          <div key={label} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{label}</span>
            <span className={`font-semibold ${color}`}>{value}</span>
          </div>
        ))}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Collection Rate</span>
            <span className="font-semibold">{rate}%</span>
          </div>
          <Progress value={rate} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
