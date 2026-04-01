'use client';

import { useSchoolContext } from '@/hooks/useSchoolContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { School, Calendar, Layers, Globe } from 'lucide-react';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export function SchoolOverview() {
  const school = useSchoolContext();

  if (!school) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-3">
            <div className="h-5 w-40 bg-muted animate-pulse rounded" />
            <div className="h-4 w-60 bg-muted animate-pulse rounded" />
            <div className="h-4 w-48 bg-muted animate-pulse rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const info = [
    { icon: School, label: 'School Type', value: school.school.type.charAt(0).toUpperCase() + school.school.type.slice(1) },
    { icon: Layers, label: 'Terms per Year', value: String(school.academic.terms_per_year) },
    { icon: Calendar, label: 'Academic Year Starts', value: MONTHS[(school.academic.year_start_month - 1) % 12] },
    { icon: Globe, label: 'Timezone', value: school.regional.timezone },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{school.school.name}</CardTitle>
          <Badge variant="secondary" className="capitalize">
            {school.subscription.tier}
          </Badge>
        </div>
        {school.school.config.motto && (
          <p className="text-sm text-muted-foreground italic">
            &ldquo;{school.school.config.motto}&rdquo;
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {info.map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-center gap-3">
            <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="text-sm text-muted-foreground">{label}:</span>
            <span className="text-sm font-medium">{value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
