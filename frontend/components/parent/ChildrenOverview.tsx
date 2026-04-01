'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { GraduationCap } from 'lucide-react';

interface Child {
  id: string;
  first_name: string;
  last_name: string;
  grade_level: string;
  class_name: string;
  status: string;
}

export function ChildrenOverview() {
  const { user } = useAuth();

  const { data: children = [], isLoading } = useQuery<Child[]>({
    queryKey: ['parent-children', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/parent/children');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <GraduationCap className="h-5 w-5" /> My Children
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-1.5">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))
        ) : children.length === 0 ? (
          <p className="text-sm text-muted-foreground">No children linked to your account.</p>
        ) : (
          children.map((child) => (
            <div key={child.id} className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-sm">
                {child.first_name[0]}{child.last_name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{child.first_name} {child.last_name}</p>
                <p className="text-xs text-muted-foreground">{child.grade_level} &middot; {child.class_name}</p>
              </div>
              <Badge variant={child.status === 'active' ? 'default' : 'secondary'}>
                {child.status}
              </Badge>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
