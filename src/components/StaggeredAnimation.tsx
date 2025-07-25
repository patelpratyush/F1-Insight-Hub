import React, { useState, useEffect, ReactNode } from 'react';

interface StaggeredAnimationProps {
  children: ReactNode[];
  className?: string;
  itemClassName?: string;
  delay?: number;
  staggerDelay?: number;
}

const StaggeredAnimation: React.FC<StaggeredAnimationProps> = ({ 
  children, 
  className = "",
  itemClassName = "",
  delay = 0,
  staggerDelay = 100
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div className={className}>
      {children.map((child, index) => (
        <div
          key={index}
          className={`transition-all duration-700 transform ${
            isVisible 
              ? 'translate-y-0 opacity-100' 
              : 'translate-y-12 opacity-0'
          } ${itemClassName}`}
          style={{ 
            transitionDelay: `${delay + index * staggerDelay}ms` 
          }}
        >
          {child}
        </div>
      ))}
    </div>
  );
};

export default StaggeredAnimation;