import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard';
import { FeatureGate } from '@/components/FeatureGate';

export default function AnalyticsPage() {
  return (
    <FeatureGate requiredModule="advanced_reporting">
      <AnalyticsDashboard />
    </FeatureGate>
  );
}