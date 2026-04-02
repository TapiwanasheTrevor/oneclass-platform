'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface BulkImportDialogProps {
  onImportComplete: () => void;
  onCancel: () => void;
}

export function BulkImportDialog({
  onImportComplete,
  onCancel,
}: BulkImportDialogProps) {
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <p className="text-sm text-muted-foreground">
          Bulk import UI is being consolidated into the new onboarding pipeline.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={onImportComplete}>
            Mark Complete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
