'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface UserProfileDialogProps {
  user: {
    first_name?: string;
    last_name?: string;
    email?: string;
    status?: string;
  };
  onUpdate: (updates: Record<string, unknown>) => void;
  onClose: () => void;
}

export function UserProfileDialog({
  user,
  onUpdate,
  onClose,
}: UserProfileDialogProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="profile-first-name">First Name</Label>
          <Input id="profile-first-name" defaultValue={user.first_name ?? ''} readOnly />
        </div>
        <div className="space-y-2">
          <Label htmlFor="profile-last-name">Last Name</Label>
          <Input id="profile-last-name" defaultValue={user.last_name ?? ''} readOnly />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="profile-email">Email</Label>
        <Input id="profile-email" defaultValue={user.email ?? ''} readOnly />
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
        <Button onClick={() => onUpdate({ status: user.status })}>
          Save
        </Button>
      </div>
    </div>
  );
}
