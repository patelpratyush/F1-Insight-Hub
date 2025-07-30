import React from 'react';
import LoadingSpinner from './loading-spinner';
import ErrorDisplay from './error-display';
import { cn } from '@/lib/utils';

interface DataWrapperProps {
  loading: boolean;
  error: string | null;
  data: any;
  onRetry?: () => void;
  isRetrying?: boolean;
  children: React.ReactNode;
  loadingMessage?: string;
  errorTitle?: string;
  errorVariant?: 'card' | 'inline' | 'minimal';
  className?: string;
  minHeight?: string;
  fallbackContent?: React.ReactNode;
}

const DataWrapper: React.FC<DataWrapperProps> = ({
  loading,
  error,
  data,
  onRetry,
  isRetrying = false,
  children,
  loadingMessage = 'Loading...',
  errorTitle = 'Failed to load data',
  errorVariant = 'inline',
  className = '',
  minHeight = 'min-h-[200px]',
  fallbackContent
}) => {
  const containerClasses = cn(
    'flex items-center justify-center',
    minHeight,
    className
  );

  if (loading) {
    return (
      <div className={containerClasses}>
        <LoadingSpinner message={loadingMessage} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={containerClasses}>
        <ErrorDisplay
          title={errorTitle}
          message={error}
          onRetry={onRetry}
          isRetrying={isRetrying}
          variant={errorVariant}
        />
      </div>
    );
  }

  if (!data || (Array.isArray(data) && data.length === 0)) {
    if (fallbackContent) {
      return <>{fallbackContent}</>;
    }
    
    return (
      <div className={containerClasses}>
        <div className="text-center">
          <div className="text-gray-400 text-lg mb-2">No data available</div>
          <p className="text-gray-500 text-sm">
            There's no data to display at the moment.
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 text-blue-400 hover:text-blue-300 text-sm underline"
              disabled={isRetrying}
            >
              {isRetrying ? 'Refreshing...' : 'Refresh'}
            </button>
          )}
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default DataWrapper;