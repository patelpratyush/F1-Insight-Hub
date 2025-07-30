import React from 'react';
import { AlertCircle, RefreshCw, Wifi } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ErrorDisplayProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
  variant?: 'card' | 'inline' | 'minimal';
  showRetry?: boolean;
  isRetrying?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title = 'Something went wrong',
  message = 'Unable to load data. Please check your connection and try again.',
  onRetry,
  className = '',
  variant = 'card',
  showRetry = true,
  isRetrying = false
}) => {
  const getErrorIcon = () => {
    if (message.toLowerCase().includes('network') || message.toLowerCase().includes('connection')) {
      return <Wifi className="h-12 w-12 text-red-500" />;
    }
    return <AlertCircle className="h-12 w-12 text-red-500" />;
  };

  const content = (
    <div className="flex flex-col items-center justify-center text-center space-y-4">
      {variant !== 'minimal' && getErrorIcon()}
      <div>
        <h3 className={cn(
          'font-semibold text-gray-200',
          variant === 'minimal' ? 'text-sm' : 'text-lg'
        )}>
          {title}
        </h3>
        <p className={cn(
          'text-gray-400 mt-1',
          variant === 'minimal' ? 'text-xs' : 'text-sm'
        )}>
          {message}
        </p>
      </div>
      {showRetry && onRetry && (
        <Button
          onClick={onRetry}
          disabled={isRetrying}
          variant="outline"
          size={variant === 'minimal' ? 'sm' : 'default'}
          className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
        >
          {isRetrying ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Retrying...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </>
          )}
        </Button>
      )}
    </div>
  );

  if (variant === 'card') {
    return (
      <Card className={cn('bg-gray-800/50 border-gray-700', className)}>
        <CardContent className="p-8">
          {content}
        </CardContent>
      </Card>
    );
  }

  if (variant === 'inline') {
    return (
      <div className={cn('bg-gray-800/30 border border-gray-700 rounded-lg p-6', className)}>
        {content}
      </div>
    );
  }

  return (
    <div className={cn('py-4', className)}>
      {content}
    </div>
  );
};

export default ErrorDisplay;