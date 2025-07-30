import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '', 
  message 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className={cn('flex flex-col items-center justify-center space-y-3', className)}>
      <div 
        className={cn(
          'border-4 border-gray-300 border-t-red-500 rounded-full animate-spin',
          sizeClasses[size]
        )}
      />
      {message && (
        <p className="text-gray-400 text-sm text-center">{message}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;