import React, { useState, useEffect, ReactNode } from 'react';

interface AnimatedPageWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

const AnimatedPageWrapper: React.FC<AnimatedPageWrapperProps> = ({ 
  children, 
  className = "", 
  delay = 0 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div 
      className={`transition-all duration-1000 transform ${
        isVisible 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-8 opacity-0'
      } ${className}`}
    >
      {children}
    </div>
  );
};

export default AnimatedPageWrapper;