import React from 'react';
import { cn } from '../../lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  glow?: boolean;
  pulse?: boolean;
}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', glow = false, pulse = false, children, ...props }, ref) => {
    const variants = {
      default: 'bg-secondary text-foreground border-border',
      success: 'status-active',
      warning: 'status-warning',
      error: 'status-error',
      info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    };

    const glowStyles = {
      success: 'glow-lime',
      warning: 'glow-amber',
      error: 'shadow-lg shadow-red-500/30',
      info: 'shadow-lg shadow-blue-500/30',
      default: '',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md',
          'text-xs font-medium font-mono border',
          variants[variant],
          glow && glowStyles[variant],
          pulse && 'animate-pulse-glow',
          className
        )}
        {...props}
      >
        {pulse && (
          <span className={cn(
            'w-1.5 h-1.5 rounded-full',
            variant === 'success' && 'bg-lime',
            variant === 'warning' && 'bg-amber',
            variant === 'error' && 'bg-red-500',
            variant === 'info' && 'bg-blue-400',
            variant === 'default' && 'bg-foreground'
          )} />
        )}
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';
