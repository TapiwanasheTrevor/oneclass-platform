import { Metadata } from 'next';
import CarePackageSelector from '@/components/migration/CarePackageSelector';

export const metadata: Metadata = {
  title: 'Migration Services - OneClass Platform',
  description: 'Professional data migration services for schools transitioning to OneClass platform',
};

export default function MigrationPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <CarePackageSelector />
    </div>
  );
}