import React from 'react';
import { type LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface IconButtonProps {
  icon: LucideIcon;
  variant?: 'ghost' | 'outline' | 'solid' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  tooltip?: string;
  pulse?: boolean;
  glow?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon: Icon,
      variant = 'ghost',
      size = 'md',
      tooltip,
      pulse = false,
      glow = false,
      className,
      disabled,
      onClick,
      type = 'button',
    },
    ref
  ) => {
    const variantClasses = {
      ghost: 'hover:bg-electric/10 text-muted-foreground hover:text-electric',
      outline: 'border border-border hover:border-electric/50 hover:bg-electric/10 text-foreground hover:text-electric',
      solid: 'bg-electric/20 hover:bg-electric/30 text-electric border border-electric/50',
      danger: 'hover:bg-red-500/10 text-red-500/70 hover:text-red-500 border border-red-500/20 hover:border-red-500/50',
      success: 'hover:bg-lime/10 text-lime/70 hover:text-lime border border-lime/20 hover:border-lime/50',
    };

    const sizeClasses = {
      sm: 'h-8 w-8 p-1.5',
      md: 'h-10 w-10 p-2',
      lg: 'h-12 w-12 p-2.5',
    };

    const iconSizeClasses = {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
    };

    const glowClasses = glow
      ? variant === 'danger'
        ? 'shadow-lg shadow-red-500/30'
        : variant === 'success'
        ? 'shadow-lg shadow-lime/30'
        : 'shadow-lg shadow-electric/30'
      : '';

    const button = (
      <button
        ref={ref}
        type={type}
        onClick={onClick}
        className={cn(
          'relative inline-flex items-center justify-center rounded-lg',
          'transition-all duration-200 ease-in-out',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'focus:outline-none focus:ring-2 focus:ring-electric/50',
          'hover:scale-105 active:scale-95',
          variantClasses[variant],
          sizeClasses[size],
          glowClasses,
          pulse && 'animate-pulse-glow',
          className
        )}
        disabled={disabled}
      >
        <Icon className={cn(iconSizeClasses[size], 'transition-transform')} />
      </button>
    );

    if (tooltip) {
      return (
        <div className="relative group">
          {button}
          <div
            className={cn(
              'absolute left-1/2 -translate-x-1/2 bottom-full mb-2',
              'px-2 py-1 text-xs font-medium text-foreground bg-secondary',
              'border border-border rounded shadow-lg',
              'opacity-0 group-hover:opacity-100 pointer-events-none',
              'transition-opacity duration-200',
              'whitespace-nowrap z-50'
            )}
          >
            {tooltip}
            <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-4 border-transparent border-t-secondary" />
          </div>
        </div>
      );
    }

    return button;
  }
);

IconButton.displayName = 'IconButton';
