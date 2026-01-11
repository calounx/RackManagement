import React from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../../lib/utils';

export interface StatItem {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  description?: string;
}

export interface StatsDashboardProps {
  stats: StatItem[];
  columns?: 1 | 2 | 3 | 4;
  className?: string;
  animated?: boolean;
}

/**
 * StatsDashboard Component
 *
 * A responsive dashboard for displaying statistics with icons, values, and optional trends.
 * Supports 1-4 column layouts with automatic responsive behavior.
 *
 * @example
 * <StatsDashboard
 *   stats={[
 *     {
 *       icon: Database,
 *       label: "Total Types",
 *       value: deviceTypes.length,
 *       color: "#00eaff"
 *     },
 *     {
 *       icon: TrendingUp,
 *       label: "Active Models",
 *       value: 150,
 *       color: "#10b981",
 *       trend: { value: 12, isPositive: true }
 *     }
 *   ]}
 *   columns={3}
 * />
 */
export const StatsDashboard: React.FC<StatsDashboardProps> = ({
  stats,
  columns = 3,
  className,
  animated = true,
}) => {
  const gridClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-4', gridClasses[columns], className)}>
      {stats.map((stat, index) => (
        <StatCard
          key={`${stat.label}-${index}`}
          stat={stat}
          index={index}
          animated={animated}
        />
      ))}
    </div>
  );
};

interface StatCardProps {
  stat: StatItem;
  index: number;
  animated: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ stat, index, animated }) => {
  const Icon = stat.icon;
  const iconColor = stat.color || '#6b7280';

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        delay: index * 0.05,
        duration: 0.3,
      },
    },
  };

  return (
    <motion.div
      variants={animated ? cardVariants : undefined}
      initial={animated ? 'hidden' : undefined}
      animate={animated ? 'visible' : undefined}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
      className="p-4 glass rounded-lg border border-border group hover:border-electric-blue/30 transition-all"
    >
      <div className="flex items-center justify-between">
        {/* Left Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-mono font-bold text-electric">
              {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
            </p>
            {stat.trend && (
              <span
                className={cn(
                  'text-xs font-medium px-1.5 py-0.5 rounded',
                  stat.trend.isPositive
                    ? 'text-lime bg-lime/10'
                    : 'text-red-400 bg-red-500/10'
                )}
              >
                {stat.trend.isPositive ? '+' : ''}
                {stat.trend.value}%
              </span>
            )}
          </div>
          {stat.description && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              {stat.description}
            </p>
          )}
        </div>

        {/* Icon */}
        <div
          className="flex-shrink-0 ml-3 w-12 h-12 rounded-xl flex items-center justify-center border-2 transition-all group-hover:scale-110"
          style={{
            backgroundColor: `${iconColor}10`,
            borderColor: `${iconColor}40`,
          }}
        >
          <Icon
            className="w-6 h-6"
            style={{ color: iconColor }}
          />
        </div>
      </div>
    </motion.div>
  );
};

export interface MiniStatProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
  className?: string;
}

/**
 * MiniStat Component
 *
 * A compact stat display for inline use or smaller spaces.
 *
 * @example
 * <MiniStat
 *   icon={Box}
 *   label="Models"
 *   value={42}
 *   color="#00eaff"
 * />
 */
export const MiniStat: React.FC<MiniStatProps> = ({
  icon: Icon,
  label,
  value,
  color = '#6b7280',
  className,
}) => {
  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      <div
        className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border"
        style={{
          backgroundColor: `${color}10`,
          borderColor: `${color}40`,
        }}
      >
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div>
        <p className="text-xs text-muted-foreground leading-none">{label}</p>
        <p className="text-sm font-mono font-semibold text-foreground mt-0.5">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
      </div>
    </div>
  );
};
