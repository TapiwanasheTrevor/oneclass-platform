'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageSquare } from 'lucide-react';
import Link from 'next/link';

interface Message {
  id: string;
  sender_name: string;
  subject: string;
  preview: string;
  sent_at: string;
  is_read: boolean;
}

export function CommunicationCenter() {
  const { user } = useAuth();

  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ['parent-messages', user?.id],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications/messages');
      return res.data;
    },
    enabled: !!user,
    retry: 1,
    staleTime: 60_000,
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
          <MessageSquare className="h-5 w-5" /> Messages
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-full" />
            </div>
          ))
        ) : messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">No messages yet.</p>
        ) : (
          messages.slice(0, 5).map((msg) => (
            <Link
              key={msg.id}
              href={`/parent/messages/${msg.id}`}
              className="block rounded-md p-2 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <p className={`text-sm truncate ${msg.is_read ? '' : 'font-semibold'}`}>{msg.subject}</p>
                <span className="text-xs text-muted-foreground shrink-0 ml-2">{timeAgo(msg.sent_at)}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">From: {msg.sender_name}</p>
              <p className="text-xs text-muted-foreground truncate mt-0.5">{msg.preview}</p>
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}
