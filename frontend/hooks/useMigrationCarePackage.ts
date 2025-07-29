import { useState, useEffect } from 'react';

export type MigrationDecision = 'pending' | 'no' | 'later' | 'selected';
export type PackageType = 'foundation' | 'growth' | 'enterprise' | null;

interface MigrationCarePackageState {
  decision: MigrationDecision;
  selectedPackage: PackageType;
  lastPrompted: string | null;
  purchaseCompleted: boolean;
}

const STORAGE_KEY = 'oneclass_migration_care_package';
const PROMPT_COOLDOWN_DAYS = 7; // Days before showing "Ask Me Later" again

export function useMigrationCarePackage() {
  const [state, setState] = useState<MigrationCarePackageState>({
    decision: 'pending',
    selectedPackage: null,
    lastPrompted: null,
    purchaseCompleted: false,
  });

  const [shouldShowModal, setShouldShowModal] = useState(false);

  // Load state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    console.log('Loading migration state from localStorage:', stored);
    if (stored) {
      try {
        const parsedState = JSON.parse(stored);
        console.log('Parsed migration state:', parsedState);
        setState(parsedState);
      } catch (error) {
        console.error('Failed to parse migration care package state:', error);
        // Reset to default state if parsing fails
        setState({
          decision: 'pending',
          selectedPackage: null,
          lastPrompted: null,
          purchaseCompleted: false,
        });
      }
    } else {
      console.log('No stored migration state found, using default');
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  // Determine if modal should be shown
  useEffect(() => {
    const shouldShow = shouldShowMigrationModal(state);
    console.log('Migration Modal Decision:', {
      state,
      shouldShow,
      decision: state.decision,
      purchaseCompleted: state.purchaseCompleted
    });
    setShouldShowModal(shouldShow);
  }, [state]);

  const shouldShowMigrationModal = (currentState: MigrationCarePackageState): boolean => {
    // Never show if user explicitly said NO
    if (currentState.decision === 'no') {
      return false;
    }

    // Never show if purchase is completed
    if (currentState.purchaseCompleted) {
      return false;
    }

    // Always show if pending (first time)
    if (currentState.decision === 'pending') {
      return true;
    }

    // For "Ask Me Later", check if cooldown period has passed
    if (currentState.decision === 'later' && currentState.lastPrompted) {
      const lastPromptedDate = new Date(currentState.lastPrompted);
      const now = new Date();
      const daysSinceLastPrompt = Math.floor(
        (now.getTime() - lastPromptedDate.getTime()) / (1000 * 60 * 60 * 24)
      );
      
      return daysSinceLastPrompt >= PROMPT_COOLDOWN_DAYS;
    }

    return false;
  };

  const setDecision = (decision: MigrationDecision, packageType?: PackageType) => {
    setState(prev => ({
      ...prev,
      decision,
      selectedPackage: packageType || prev.selectedPackage,
      lastPrompted: new Date().toISOString(),
    }));
  };

  const markPurchaseCompleted = () => {
    setState(prev => ({
      ...prev,
      purchaseCompleted: true,
      decision: 'selected',
    }));
  };

  const resetState = () => {
    console.log('Resetting migration care package state');
    setState({
      decision: 'pending',
      selectedPackage: null,
      lastPrompted: null,
      purchaseCompleted: false,
    });
    localStorage.removeItem(STORAGE_KEY);
  };

  // Expose reset function to window for debugging
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).resetMigrationState = resetState;
      console.log('Migration state reset function available: window.resetMigrationState()');
    }
  }, []);

  const dismissModal = () => {
    setShouldShowModal(false);
  };

  // Check if user should be blocked from accessing dashboard
  const shouldBlockDashboard = (): boolean => {
    // Block if modal should be shown (user hasn't made a decision)
    return shouldShowModal;
  };

  return {
    state,
    shouldShowModal,
    shouldBlockDashboard: shouldBlockDashboard(),
    setDecision,
    markPurchaseCompleted,
    resetState,
    dismissModal,
  };
}

// Utility function to get package details
export const getPackageDetails = (packageType: PackageType) => {
  const packages = {
    foundation: {
      name: 'Foundation Package',
      price: '$2,800',
      description: 'Perfect for small schools (50-200 students)',
      maxStudents: 200,
      features: [
        'Student records migration',
        'Staff setup (15 users)',
        '4-hour training',
        '30-day support'
      ]
    },
    growth: {
      name: 'Growth Package',
      price: '$6,500',
      description: 'Ideal for medium schools (200-800 students)',
      maxStudents: 800,
      features: [
        'Complete migration (3-year history)',
        'Financial data migration',
        '12-hour training',
        '90-day priority support'
      ]
    },
    enterprise: {
      name: 'Enterprise Package',
      price: '$15,000',
      description: 'Complete solution for large schools (800+ students)',
      maxStudents: 9999,
      features: [
        '5+ years historical data',
        'Government system integration',
        '24-hour training',
        '6-month dedicated support'
      ]
    }
  };

  return packageType ? packages[packageType] : null;
};
