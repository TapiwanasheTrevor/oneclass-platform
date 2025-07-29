"use client"

import { useMigrationCarePackage } from '@/hooks/useMigrationCarePackage';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import MigrationCarePackageModal from '@/components/migration/MigrationCarePackageModal';

export default function TestMigrationPage() {
  const {
    state,
    shouldShowModal,
    shouldBlockDashboard,
    setDecision,
    resetState,
    dismissModal
  } = useMigrationCarePackage();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">Migration Care Package Test</h1>
        
        <Card>
          <CardHeader>
            <CardTitle>Current State</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(state, null, 2)}
            </pre>
            <div className="mt-4 space-y-2">
              <p><strong>Should Show Modal:</strong> {shouldShowModal ? 'YES' : 'NO'}</p>
              <p><strong>Should Block Dashboard:</strong> {shouldBlockDashboard ? 'YES' : 'NO'}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Test Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={resetState} variant="destructive">
              Reset State (Clear localStorage)
            </Button>
            
            <Button onClick={() => setDecision('pending')} variant="outline">
              Set to Pending
            </Button>
            
            <Button onClick={() => setDecision('later')} variant="outline">
              Set to Ask Me Later
            </Button>
            
            <Button onClick={() => setDecision('no')} variant="outline">
              Set to No
            </Button>
            
            <Button onClick={() => setDecision('selected', 'growth')} variant="outline">
              Set to Selected (Growth Package)
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>localStorage Debug</CardTitle>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => {
                const stored = localStorage.getItem('oneclass_migration_care_package');
                alert(`localStorage value: ${stored}`);
              }}
              variant="outline"
            >
              Check localStorage
            </Button>
            
            <Button 
              onClick={() => {
                localStorage.removeItem('oneclass_migration_care_package');
                window.location.reload();
              }}
              variant="destructive"
              className="ml-2"
            >
              Clear localStorage & Reload
            </Button>
          </CardContent>
        </Card>

        {/* Modal Test */}
        {shouldShowModal && (
          <MigrationCarePackageModal
            isOpen={shouldShowModal}
            onClose={(decision) => {
              console.log('Modal closed with decision:', decision);
              setDecision(decision);
              dismissModal();
            }}
            onSelectPackage={(packageType) => {
              console.log('Selected package:', packageType);
            }}
          />
        )}
      </div>
    </div>
  );
}
