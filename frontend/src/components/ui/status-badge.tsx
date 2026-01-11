import React from 'react';
import { type LucideIcon, CheckCircle, AlertCircle, AlertTriangle, Info, Activity, Circle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';

export interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'active' | 'inactive' | 'maintenance';
  label?: string;
  icon?: LucideIcon;
  pulse?: boolean;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const statusConfig = {
  success: {
    icon: CheckCircle,
    classes: 'bg-lime/20 text-lime border-lime/50',
    glowClasses: 'shadow-lg shadow-lime/30',
  },
  warning: {
    icon: AlertTriangle,
    classes: 'bg-amber/20 text-amber border-amber/50',
    glowClasses: 'shadow-lg shadow-amber/30',
  },
  error: {
    icon: AlertCircle,
    classes: 'bg-red-500/20 text-red-500 border-red-500/50',
    glowClasses: 'shadow-lg shadow-red-500/30',
  },
  info: {
    icon: Info,
    classes: 'bg-blue-500/20 text-blue-500 border-blue-500/50',
    glowClasses: 'shadow-lg shadow-blue-500/30',
  },
  active: {
    icon: Activity,
    classes: 'bg-lime/20 text-lime border-lime/50',
    glowClasses: 'shadow-lg shadow-lime/30',
  },
  inactive: {
    icon: Circle,
    classes: 'bg-muted/20 text-muted-foreground border-border',
    glowClasses: '',
  },
  maintenance: {
    icon: AlertTriangle,
    classes: 'bg-amber/20 text-amber border-amber/50',
    glowClasses: 'shadow-lg shadow-amber/30',
  },
};

const sizeClasses = {
  sm: {
    container: 'px-2 py-0.5 text-xs gap-1',
    icon: 'h-3 w-3',
  },
  md: {
    container: 'px-2.5 py-1 text-sm gap-1.5',
    icon: 'h-4 w-4',
  },
  lg: {
    container: 'px-3 py-1.5 text-base gap-2',
    icon: 'h-5 w-5',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  icon: CustomIcon,
  pulse = false,
  showIcon = true,
  size = 'md',
  className,
}) => {
  const config = statusConfig[status];
  const Icon = CustomIcon || config.icon;
  const sizeConfig = sizeClasses[size];
  const displayLabel = label || status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <motion.div
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        'transition-all duration-200',
        config.classes,
        sizeConfig.container,
        pulse && 'animate-pulse-glow',
        pulse && config.glowClasses,
        className
      )}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
    >
      {showIcon && Icon && (
        <Icon
          className={cn(
            sizeConfig.icon,
            pulse && 'animate-pulse'
          )}
        />
      )}
      {displayLabel && <span>{displayLabel}</span>}
    </motion.div>
  );
};

export interface StatusIndicatorProps {
  status: 'active' | 'error' | 'warning' | 'inactive';
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const indicatorSizeClasses = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

const indicatorColorClasses = {
  active: 'bg-lime glow-lime',
  error: 'bg-red-500',
  warning: 'bg-amber glow-amber',
  inactive: 'bg-muted-foreground/50',
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  pulse = true,
  size = 'md',
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-full',
        indicatorSizeClasses[size],
        indicatorColorClasses[status],
        pulse && status !== 'inactive' && 'animate-pulse-glow',
        className
      )}
    />
  );
};
