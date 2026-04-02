'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface UserInviteFormProps {
  onUserInvited: () => void;
  onCancel: () => void;
}

export function UserInviteForm({ onUserInvited, onCancel }: UserInviteFormProps) {
  const [email, setEmail] = useState('');

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="invite-email">Email</Label>
        <Input
          id="invite-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@school.edu"
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={onUserInvited} disabled={!email.trim()}>
          Send Invite
        </Button>
      </div>
    </div>
  );
}
