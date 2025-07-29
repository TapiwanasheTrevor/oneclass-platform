import { Metadata } from 'next';
import SuperAdminDashboard from '@/components/migration/SuperAdminDashboard';

export const metadata: Metadata = {
  title: 'Migration Services Admin - OneClass Platform',
  description: 'Super admin dashboard for managing migration services and care packages',
};

export default function AdminMigrationPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <SuperAdminDashboard />
    </div>
  );
}