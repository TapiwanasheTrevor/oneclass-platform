// =====================================================
// Error Boundary Components
// File: frontend/components/ui/error-boundary.tsx
// =====================================================

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, ArrowLeft, Bug, Wifi, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to console for development
    console.error('Error Boundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send this to an error reporting service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <AlertTriangle className="w-16 h-16 text-red-500" />
              </div>
              <CardTitle className="text-red-900">Something went wrong</CardTitle>
              <CardDescription>
                We encountered an unexpected error. Our team has been notified.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center space-y-2">
                <Button onClick={this.handleRetry} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => window.location.href = '/dashboard'}
                  className="w-full"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </Button>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4">
                  <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">
                    Technical Details (Dev Mode)
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-800 max-h-40 overflow-y-auto">
                    <div className="font-bold mb-2">Error:</div>
                    <div className="mb-4">{this.state.error.message}</div>
                    <div className="font-bold mb-2">Stack Trace:</div>
                    <div className="whitespace-pre-wrap">{this.state.error.stack}</div>
                  </div>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Specific error components for different scenarios
interface ErrorMessageProps {
  title?: string;
  message?: string;
  type?: 'network' | 'auth' | 'permission' | 'validation' | 'generic';
  onRetry?: () => void;
  onGoBack?: () => void;
  className?: string;
}

export function ErrorMessage({ 
  title, 
  message, 
  type = 'generic', 
  onRetry, 
  onGoBack,
  className = '' 
}: ErrorMessageProps) {
  const getIcon = () => {
    switch (type) {
      case 'network':
        return <Wifi className="w-8 h-8 text-red-500" />;
      case 'auth':
        return <Shield className="w-8 h-8 text-red-500" />;
      case 'permission':
        return <Shield className="w-8 h-8 text-red-500" />;
      case 'validation':
        return <AlertTriangle className="w-8 h-8 text-yellow-500" />;
      default:
        return <Bug className="w-8 h-8 text-red-500" />;
    }
  };

  const getDefaultTitle = () => {
    switch (type) {
      case 'network':
        return 'Connection Error';
      case 'auth':
        return 'Authentication Required';
      case 'permission':
        return 'Access Denied';
      case 'validation':
        return 'Invalid Data';
      default:
        return 'Error';
    }
  };

  const getDefaultMessage = () => {
    switch (type) {
      case 'network':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case 'auth':
        return 'You need to sign in to access this page.';
      case 'permission':
        return 'You don\'t have permission to access this resource.';
      case 'validation':
        return 'Please check your input and try again.';
      default:
        return 'An unexpected error occurred. Please try again later.';
    }
  };

  return (
    <Card className={className}>
      <CardContent className="p-6 text-center">
        <div className="flex justify-center mb-4">
          {getIcon()}
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {title || getDefaultTitle()}
        </h3>
        <p className="text-gray-600 mb-6">
          {message || getDefaultMessage()}
        </p>
        <div className="flex justify-center space-x-3">
          {onRetry && (
            <Button onClick={onRetry}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          )}
          {onGoBack && (
            <Button variant="outline" onClick={onGoBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function NetworkError({ onRetry, className = '' }: { onRetry?: () => void; className?: string }) {
  return (
    <ErrorMessage
      type="network"
      onRetry={onRetry}
      className={className}
    />
  );
}

export function AuthError({ onRetry, className = '' }: { onRetry?: () => void; className?: string }) {
  return (
    <ErrorMessage
      type="auth"
      onRetry={onRetry}
      onGoBack={() => window.location.href = '/login'}
      className={className}
    />
  );
}

export function PermissionError({ className = '' }: { className?: string }) {
  return (
    <ErrorMessage
      type="permission"
      onGoBack={() => window.history.back()}
      className={className}
    />
  );
}

export function ValidationError({ message, onRetry, className = '' }: { 
  message?: string; 
  onRetry?: () => void; 
  className?: string;
}) {
  return (
    <ErrorMessage
      type="validation"
      message={message}
      onRetry={onRetry}
      className={className}
    />
  );
}

// Page-level error component
export function PageError({ 
  error, 
  reset 
}: { 
  error: Error; 
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <AlertTriangle className="w-16 h-16 text-red-500" />
          </div>
          <CardTitle className="text-red-900">Page Error</CardTitle>
          <CardDescription>
            This page encountered an error and could not be displayed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error.message || 'An unexpected error occurred while loading this page.'}
            </AlertDescription>
          </Alert>
          
          <div className="flex space-x-3">
            <Button onClick={reset} className="flex-1">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
            <Button 
              variant="outline" 
              onClick={() => window.location.href = '/dashboard'}
              className="flex-1"
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Component error boundary wrapper
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WrappedComponent(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}