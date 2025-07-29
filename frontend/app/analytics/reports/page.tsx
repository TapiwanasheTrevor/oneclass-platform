import { ReportsManagement } from '@/components/analytics/ReportsManagement';
import { FeatureGate } from '@/components/FeatureGate';

export default function ReportsPage() {
  return (
    <FeatureGate requiredModule="advanced_reporting">
      <ReportsManagement />
    </FeatureGate>
  );
}